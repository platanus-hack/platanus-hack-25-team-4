import { COLLISION_CONFIG } from "../config/collision.config.js";
import { getRedisClient } from "../infrastructure/redis.js";
import { prisma } from "../lib/prisma.js";
import { enqueueMission } from "../src/interview/missionQueue.js";
import type { InterviewMission } from "../src/interview/types.js";
import { MatchType, MatchStatus } from "../types/index.js";
import type { Match } from "../types/match.type.js";
import type { UserProfile } from "../types/user.type.js";
import { logger } from "../utils/logger.util.js";


export interface DetectedCollision {
  circle1Id: string | null; // Null when visitor doesn't have a circle
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distance: number;
  timestamp: number;
}

export interface MissionResultJudgeDecision {
  /**
   * Optional short natural-language summary of the agent-to-agent conversation.
   * When present, it should start with: "Summary of agent interaction: ..."
   */
  summary_text?: string;
  // Allow additional fields without enforcing structure here
  [key: string]: unknown;
}

export interface MissionResult {
  success: boolean;
  matchMade: boolean;
  transcript?: string;
  judgeDecision?: MissionResultJudgeDecision;
  error?: string;
}

export interface CooldownStatus {
  allowed: boolean;
  reason?: string;
  remainingMs?: number;
  cooldownType?: "rejected" | "matched" | "notified";
}

function parseUserProfile(profile: unknown): UserProfile {
  if (profile && typeof profile === "object" && !Array.isArray(profile)) {
    const obj = profile;
    return {
      bio: "bio" in obj && typeof obj.bio === "string" ? obj.bio : undefined,
      socialStyle: "socialStyle" in obj && typeof obj.socialStyle === "string" ? obj.socialStyle : undefined,
      interests: "interests" in obj && Array.isArray(obj.interests) ? obj.interests : undefined,
      profileCompleted: "profileCompleted" in obj && typeof obj.profileCompleted === "boolean" ? obj.profileCompleted : undefined,
      boundaries: "boundaries" in obj && Array.isArray(obj.boundaries) ? obj.boundaries : undefined,
      availability: "availability" in obj && typeof obj.availability === "string" ? obj.availability : undefined,
    };
  }
  return {};
}

function toMatch(prismaMatch: {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  primaryCircleId: string;
  secondaryCircleId: string;
  type: string;
  worthItScore: number;
  status: string;
  explanationSummary: string | null;
  collisionEventId: string | null;
  createdAt: Date;
  updatedAt: Date;
}): Match {
  let matchType: MatchType;
  if (prismaMatch.type === "match") {
    matchType = MatchType.MATCH;
  } else {
    matchType = MatchType.SOFT_MATCH;
  }

  let matchStatus: MatchStatus;
  if (prismaMatch.status === "pending_accept") {
    matchStatus = MatchStatus.PENDING_ACCEPT;
  } else if (prismaMatch.status === "active") {
    matchStatus = MatchStatus.ACTIVE;
  } else if (prismaMatch.status === "declined") {
    matchStatus = MatchStatus.DECLINED;
  } else {
    matchStatus = MatchStatus.EXPIRED;
  }

  return {
    ...prismaMatch,
    type: matchType,
    status: matchStatus,
  };
}

/**
 * Service for managing agent-based matching workflow
 * Handles cooldowns, mission creation, and match determination
 */
export class AgentMatchService {
  /**
   * Deterministically decide whether this mission should result in a
   * "lucky" match. Uses a simple hash of the missionId to approximate
   * a 10% chance while keeping behavior stable for tests and replays.
   */
  private shouldCreateLuckyMatch(missionId: string): boolean {
    if (!missionId) {
      return false;
    }

    const charCodeSum = missionId
      .split("")
      .reduce((acc, ch) => acc + ch.charCodeAt(0), 0);

    // Roughly 10% of possible sums will satisfy this condition
    return charCodeSum % 10 === 0;
  }

  /**
   * Prepare mission payload for enqueuing to BullMQ
   * Fetches user profiles and circle details
   */
  private async prepareMissionPayload(
    mission: Awaited<ReturnType<typeof prisma.interviewMission.create>>,
  ): Promise<InterviewMission> {
    // Fetch user profiles
    const [ownerUser, visitorUser] = await Promise.all([
      prisma.user.findUnique({
        where: { id: mission.ownerUserId },
        select: {
          id: true,
          firstName: true,
          lastName: true,
          profile: true,
        },
      }),
      prisma.user.findUnique({
        where: { id: mission.visitorUserId },
        select: {
          id: true,
          firstName: true,
          lastName: true,
          profile: true,
        },
      }),
    ]);

    if (!ownerUser || !visitorUser) {
      throw new Error("User not found for mission");
    }

    // Fetch circles
    const [ownerCircle, visitorCircle] = await Promise.all([
      prisma.circle.findUnique({
        where: { id: mission.ownerCircleId },
        select: {
          id: true,
          objective: true,
          radiusMeters: true,
          startAt: true,
          expiresAt: true,
        },
      }),
      prisma.circle.findUnique({
        where: { id: mission.visitorCircleId },
        select: {
          id: true,
          objective: true,
          radiusMeters: true,
          startAt: true,
          expiresAt: true,
        },
      }),
    ]);

    if (!ownerCircle || !visitorCircle) {
      throw new Error("Circle not found for mission");
    }

    // Parse profiles
    const ownerProfile = parseUserProfile(ownerUser.profile);
    const visitorProfile = parseUserProfile(visitorUser.profile);

    // Build InterviewMission payload
    return {
      mission_id: mission.id,
      owner_user_id: mission.ownerUserId,
      visitor_user_id: mission.visitorUserId,
      owner_profile: {
        id: ownerUser.id,
        display_name: `${ownerUser.firstName} ${ownerUser.lastName}`,
        motivations_and_goals: {
          primary_goal: ownerProfile.bio || "Connect with people",
        },
        conversation_micro_preferences: {
          preferred_opener_style: ownerProfile.socialStyle || "friendly",
        },
      },
      visitor_profile: {
        id: visitorUser.id,
        display_name: `${visitorUser.firstName} ${visitorUser.lastName}`,
        motivations_and_goals: {
          primary_goal: visitorProfile.bio || "Connect with people",
        },
        conversation_micro_preferences: {
          preferred_opener_style: visitorProfile.socialStyle || "friendly",
        },
      },
      owner_circle: {
        id: ownerCircle.id,
        objective_text: ownerCircle.objective,
        radius_m: ownerCircle.radiusMeters || 500,
        time_window: `${ownerCircle.startAt?.toISOString() || new Date().toISOString()} - ${ownerCircle.expiresAt?.toISOString() || new Date().toISOString()}`,
      },
      context: {
        approximate_time_iso: new Date().toISOString(),
        approximate_distance_m: 100, // Default, actual distance from collision event
      },
    };
  }

  /**
   * Check if an inverse match already exists between two users
   * Returns the existing match if found in either direction
   */
  async checkInverseMatch(
    user1Id: string,
    user2Id: string,
  ): Promise<Match | null> {
    try {
      const existingMatch = await prisma.match.findFirst({
        where: {
          OR: [
            {
              primaryUserId: user1Id,
              secondaryUserId: user2Id,
            },
            {
              primaryUserId: user2Id,
              secondaryUserId: user1Id,
            },
          ],
        },
      });

      return existingMatch ? toMatch(existingMatch) : null;
    } catch (error) {
      logger.error("Failed to check inverse match", {
        user1Id,
        user2Id,
        error,
      });
      return null;
    }
  }

  /**
   * Check if user pair has an active cooldown
   * Cooldowns are tiered based on previous match outcome
   */
  async checkCooldown(
    user1Id: string,
    user2Id: string,
  ): Promise<CooldownStatus> {
    try {
      logger.debug("[AGENT_MATCH] Checking cooldown", {
        user1Id,
        user2Id,
      });

      const redis = getRedisClient();
      const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown(
        user1Id,
        user2Id,
      );

      const cooldownData = await redis.hgetall(cooldownKey);

      if (!cooldownData || Object.keys(cooldownData).length === 0) {
        // No active cooldown
        logger.debug("[AGENT_MATCH] No active cooldown", {
          user1Id,
          user2Id,
        });
        return { allowed: true };
      }

      const cooldownTypeValue = cooldownData.type;
      const isValidCooldownType = (
        value: string | undefined,
      ): value is "rejected" | "matched" | "notified" => {
        if (value === undefined) {
          return false;
        }
        return (
          value === "rejected" || value === "matched" || value === "notified"
        );
      };
      const cooldownType: "rejected" | "matched" | "notified" | undefined =
        isValidCooldownType(cooldownTypeValue) ? cooldownTypeValue : undefined;

      const expiresAt = parseInt(cooldownData.expiresAt || "0");
      const now = Date.now();

      if (now > expiresAt) {
        // Cooldown has expired
        logger.debug("[AGENT_MATCH] Cooldown has expired, removing", {
          user1Id,
          user2Id,
          cooldownType,
        });
        await redis.del(cooldownKey);
        return { allowed: true };
      }

      const remainingMs = expiresAt - now;
      logger.warn("[AGENT_MATCH] Active cooldown prevents matching", {
        user1Id,
        user2Id,
        cooldownType,
        remainingMs,
      });
      return {
        allowed: false,
        reason: `Cooldown active (${cooldownType || "unknown"})`,
        remainingMs,
        cooldownType: cooldownType || "notified",
      };
    } catch (error) {
      logger.error("[AGENT_MATCH] Failed to check cooldown", {
        user1Id,
        user2Id,
        error,
      });
      // In case of error, allow the match to proceed (fail open)
      return { allowed: true };
    }
  }

  /**
   * Create mission for a detected collision
   * Acquires distributed lock to prevent duplicate missions
   */
  async createMissionForCollision(
    collision: DetectedCollision,
  ): Promise<Awaited<
    ReturnType<typeof prisma.interviewMission.create>
  > | null> {
    const startTime = Date.now();
    const lockIdentifier = collision.circle1Id || collision.user1Id;
    const lockKey = COLLISION_CONFIG.REDIS_KEYS.inFlightMission(
      lockIdentifier,
      collision.circle2Id,
    );
    const redis = getRedisClient();
    const workerId = `worker-${Date.now()}-${Math.random()}`;

    logger.info("[AGENT_MATCH] Starting mission creation for collision", {
      user1Id: collision.user1Id,
      user2Id: collision.user2Id,
      circle1Id: collision.circle1Id,
      circle2Id: collision.circle2Id,
      distance: collision.distance,
    });

    try {
      // Acquire distributed lock (NX = only if not exists, EX = auto-expire)
      logger.debug("[AGENT_MATCH] Attempting to acquire mission lock", {
        lockKey,
        workerId,
        ttl: COLLISION_CONFIG.IN_FLIGHT_MISSION_TTL,
      });

      const lockAcquired = await redis.set(
        lockKey,
        workerId,
        "EX",
        COLLISION_CONFIG.IN_FLIGHT_MISSION_TTL,
        "NX",
      );

      if (!lockAcquired) {
        logger.warn("[AGENT_MATCH] Mission creation already in progress (lock not acquired)", {
          lockKey,
          lockIdentifier,
          circle2Id: collision.circle2Id,
        });
        return null;
      }

      logger.debug("[AGENT_MATCH] Mission lock acquired successfully", {
        workerId,
      });

      // Check cooldown one more time before creating mission
      logger.debug("[AGENT_MATCH] Performing cooldown check before mission creation", {
        user1Id: collision.user1Id,
        user2Id: collision.user2Id,
      });
      const cooldownCheck = await this.checkCooldown(
        collision.user1Id,
        collision.user2Id,
      );

      if (!cooldownCheck.allowed) {
        logger.warn("[AGENT_MATCH] Cooldown active, skipping mission creation", {
          user1Id: collision.user1Id,
          user2Id: collision.user2Id,
          cooldown: cooldownCheck,
        });
        await redis.del(lockKey);
        return null;
      }

      logger.debug("[AGENT_MATCH] Cooldown check passed", {
        user1Id: collision.user1Id,
        user2Id: collision.user2Id,
      });

      // For missions, we need both users to have circles
      // If visitor (user1) doesn't have a circle, we need to find or create one
      let ownerCircleId = collision.circle1Id;
      if (!ownerCircleId) {
        // Get the visitor's first active circle, or skip mission creation
        logger.debug("[AGENT_MATCH] Looking for visitor's active circle", {
          visitorUserId: collision.user1Id,
        });
        const visitorCircle = await prisma.circle.findFirst({
          where: {
            userId: collision.user1Id,
            status: "active",
            expiresAt: { gt: new Date() },
          },
        });

        if (!visitorCircle) {
          logger.warn(
            "[AGENT_MATCH] Visitor has no active circles, skipping mission creation",
            {
              visitorUserId: collision.user1Id,
            },
          );
          await redis.del(lockKey);
          return null;
        }
        logger.debug("[AGENT_MATCH] Using visitor's circle for mission", {
          visitorCircleId: visitorCircle.id,
        });
        ownerCircleId = visitorCircle.id;
      }

      // Create collision event ID
      const collisionEventId = `${lockIdentifier}:${collision.circle2Id}`;

      // Create interview mission in database
      logger.debug("[AGENT_MATCH] Creating interview mission in database", {
        ownerUserId: collision.user1Id,
        visitorUserId: collision.user2Id,
        ownerCircleId: ownerCircleId,
        visitorCircleId: collision.circle2Id,
      });

      const mission = await prisma.interviewMission.create({
        data: {
          ownerUserId: collision.user1Id,
          visitorUserId: collision.user2Id,
          ownerCircleId: ownerCircleId,
          visitorCircleId: collision.circle2Id,
          collisionEventId: collisionEventId,
          status: "pending",
          attemptNumber: 1,
        },
      });

      logger.info("[AGENT_MATCH] Interview mission created in database", {
        missionId: mission.id,
        ownerUserId: mission.ownerUserId,
        visitorUserId: mission.visitorUserId,
      });

      // Try to update collision event if it exists
      try {
        if (collision.circle1Id) {
          logger.debug("[AGENT_MATCH] Updating CollisionEvent with mission ID", {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
            missionId: mission.id,
          });
          await prisma.collisionEvent.update({
            where: {
              unique_collision_pair: {
                circle1Id: collision.circle1Id,
                circle2Id: collision.circle2Id,
              },
            },
            data: {
              missionId: mission.id,
              status: "mission_created",
            },
          });
          logger.debug("[AGENT_MATCH] CollisionEvent updated successfully", {
            missionId: mission.id,
          });
        }
      } catch (error) {
        // CollisionEvent might not exist if circle1Id was null
        logger.debug("[AGENT_MATCH] CollisionEvent not found or could not be updated", {
          error,
        });
      }

      logger.info("[AGENT_MATCH] Mission created for collision", {
        missionId: mission.id,
        user1Id: collision.user1Id,
        user2Id: collision.user2Id,
        circle1Id: collision.circle1Id,
        circle2Id: collision.circle2Id,
      });

      // Enqueue the mission for processing by the interview worker
      try {
        logger.debug("[AGENT_MATCH] Preparing mission payload for enqueuing", {
          missionId: mission.id,
        });
        const missionPayload = await this.prepareMissionPayload(mission);
        await enqueueMission(missionPayload);
        logger.info("[AGENT_MATCH] Mission enqueued for interview processing", {
          missionId: mission.id,
        });
      } catch (error) {
        logger.error("[AGENT_MATCH] Failed to enqueue mission", {
          missionId: mission.id,
          error,
        });
        // Don't throw - mission is created, worker can pick it up later
      }

      const duration = Date.now() - startTime;
      logger.info("[AGENT_MATCH] Mission creation completed successfully", {
        missionId: mission.id,
        durationMs: duration,
      });

      return mission;
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error("[AGENT_MATCH] Failed to create mission for collision", {
        user1Id: collision.user1Id,
        user2Id: collision.user2Id,
        circle1Id: collision.circle1Id,
        circle2Id: collision.circle2Id,
        error,
        durationMs: duration,
      });
      // Release lock on error
      await redis.del(lockKey);
      throw error;
    }
  }

  /**
   * Set cooldown for user pair after mission completion
   * Tiered cooldown periods based on match outcome
   */
  async setCooldown(
    user1Id: string,
    user2Id: string,
    outcome: "rejected" | "matched" | "notified",
  ): Promise<void> {
    try {
      logger.debug("[AGENT_MATCH] Setting cooldown", {
        user1Id,
        user2Id,
        outcome,
      });

      const redis = getRedisClient();
      const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown(
        user1Id,
        user2Id,
      );

      // Determine cooldown duration based on outcome
      let cooldownDurationMs: number;
      switch (outcome) {
        case "rejected":
          cooldownDurationMs = COLLISION_CONFIG.COOLDOWN_DURATIONS.rejected;
          break;
        case "matched":
          cooldownDurationMs = COLLISION_CONFIG.COOLDOWN_DURATIONS.matched;
          break;
        case "notified":
        default:
          cooldownDurationMs = COLLISION_CONFIG.COOLDOWN_DURATIONS.notified;
      }

      const expiresAt = Date.now() + cooldownDurationMs;

      logger.debug("[AGENT_MATCH] Cooldown details", {
        user1Id,
        user2Id,
        outcome,
        durationMs: cooldownDurationMs,
        durationHours: (cooldownDurationMs / (60 * 60 * 1000)).toFixed(2),
        expiresAt: new Date(expiresAt).toISOString(),
      });

      await redis.hset(cooldownKey, {
        type: outcome,
        expiresAt: String(expiresAt),
        createdAt: String(Date.now()),
      });

      // Set TTL on the key itself (safety measure)
      await redis.expire(cooldownKey, Math.ceil(cooldownDurationMs / 1000));

      logger.info("[AGENT_MATCH] Cooldown set successfully", {
        user1Id,
        user2Id,
        outcome,
        expiresAt: new Date(expiresAt).toISOString(),
        durationHours: (cooldownDurationMs / (60 * 60 * 1000)).toFixed(2),
      });
    } catch (error) {
      logger.error("[AGENT_MATCH] Failed to set cooldown", {
        user1Id,
        user2Id,
        outcome,
        error,
      });
      // Don't throw - cooldown failure shouldn't block the system
    }
  }

  /**
   * Handle mission result and create match if successful
   * Called by mission worker after agent completes interview
   */
  async handleMissionResult(
    missionId: string,
    result: MissionResult,
  ): Promise<Match | null> {
    const startTime = Date.now();
    logger.info("[AGENT_MATCH] Handling mission result", {
      missionId,
      success: result.success,
      matchMade: result.matchMade,
      error: result.error,
    });

    try {
      // Fetch the mission
      logger.debug("[AGENT_MATCH] Fetching mission from database", { missionId });
      const mission = await prisma.interviewMission.findUnique({
        where: { id: missionId },
      });

      if (!mission) {
        logger.warn("[AGENT_MATCH] Mission not found for result handling", { missionId });
        return null;
      }

      logger.debug("[AGENT_MATCH] Mission found", {
        missionId,
        ownerUserId: mission.ownerUserId,
        visitorUserId: mission.visitorUserId,
        currentStatus: mission.status,
      });

      // Update mission status
      logger.debug("[AGENT_MATCH] Updating mission status", {
        missionId,
        newStatus: result.success ? "completed" : "failed",
      });
      await prisma.interviewMission.update({
        where: { id: missionId },
        data: {
          status: result.success ? "completed" : "failed",
          transcript: result.transcript
            ? typeof result.transcript === "string"
              ? JSON.parse(result.transcript)
              : result.transcript
            : undefined,
          judgeDecision: result.judgeDecision
            ? JSON.parse(JSON.stringify(result.judgeDecision))
            : undefined,
          failureReason: result.error || null,
          completedAt: new Date(),
        },
      });
      logger.debug("[AGENT_MATCH] Mission status updated", { missionId });

      if (!result.success) {
        logger.warn("[AGENT_MATCH] Mission failed", {
          missionId,
          error: result.error,
        });
        // Set cooldown for failed mission (notified outcome)
        await this.setCooldown(
          mission.ownerUserId,
          mission.visitorUserId,
          "notified",
        );
        const duration = Date.now() - startTime;
        logger.info("[AGENT_MATCH] Mission result handling completed (failed)", {
          missionId,
          durationMs: duration,
        });
        return null;
      }

      // If match was made by agent, check for inverse match first
      if (result.matchMade) {
        // Try to extract a short summary text from the judge decision
        const summaryText = (result.judgeDecision?.summary_text ?? "").trim();
        logger.info("[AGENT_MATCH] Agent determined a match should be made", {
          missionId,
          ownerUserId: mission.ownerUserId,
          visitorUserId: mission.visitorUserId,
        });

        // Use transaction to prevent race conditions
        const match = await prisma.$transaction(async (tx) => {
          // Check if inverse match already exists
          logger.debug("[AGENT_MATCH] Checking for inverse match", {
            missionId,
            ownerUserId: mission.ownerUserId,
            visitorUserId: mission.visitorUserId,
          });
          const inverseMatch = await tx.match.findFirst({
            where: {
              OR: [
                {
                  primaryUserId: mission.ownerUserId,
                  secondaryUserId: mission.visitorUserId,
                },
                {
                  primaryUserId: mission.visitorUserId,
                  secondaryUserId: mission.ownerUserId,
                },
              ],
            },
          });

          if (inverseMatch) {
            // Inverse match exists - both users have matched!
            logger.info("[AGENT_MATCH] Inverse match found - mutual match detected!", {
              missionId,
              existingMatchId: inverseMatch.id,
              ownerUserId: mission.ownerUserId,
              visitorUserId: mission.visitorUserId,
            });

            // Update the existing match to 'active'
            await tx.match.update({
              where: { id: inverseMatch.id },
              data: { status: "active" },
            });
            logger.debug("[AGENT_MATCH] Existing match activated", {
              matchId: inverseMatch.id,
            });

            // Create this match also as 'active' (to maintain symmetry in the database)
            const newMatch = await tx.match.create({
              data: {
                primaryUserId: mission.ownerUserId,
                secondaryUserId: mission.visitorUserId,
                primaryCircleId: mission.ownerCircleId,
                secondaryCircleId: mission.visitorCircleId,
                type: "match",
                worthItScore: 0.95,
                status: "active", // Active immediately due to mutual match
                explanationSummary: "Mutual agent-determined match",
                collisionEventId: `${mission.ownerCircleId}:${mission.visitorCircleId}`,
              },
            });
            logger.debug("[AGENT_MATCH] Symmetric match created", {
              newMatchId: newMatch.id,
            });

            // Create or update chat for both users
            const existingChat = await tx.chat.findFirst({
              where: {
                OR: [
                  {
                    primaryUserId: mission.ownerUserId,
                    secondaryUserId: mission.visitorUserId,
                  },
                  {
                    primaryUserId: mission.visitorUserId,
                    secondaryUserId: mission.ownerUserId,
                  },
                ],
              },
            });

            if (!existingChat) {
              const chat = await tx.chat.create({
                data: {
                  primaryUserId: mission.ownerUserId,
                  secondaryUserId: mission.visitorUserId,
                },
              });
              logger.info("[AGENT_MATCH] Chat created for mutual match", {
                user1: mission.ownerUserId,
                user2: mission.visitorUserId,
              });

              // If we have a judge summary, store it as the first chat message
              if (summaryText) {
                await tx.message.create({
                  data: {
                    chatId: chat.id,
                    senderUserId: mission.ownerUserId,
                    receiverId: mission.visitorUserId,
                    content: summaryText,
                  },
                });
              }
            }

            return newMatch;
          } else {
            // No inverse match - create pending match
            logger.info("[AGENT_MATCH] No inverse match found - creating pending match", {
              missionId,
              ownerUserId: mission.ownerUserId,
              visitorUserId: mission.visitorUserId,
            });

            const newMatch = await tx.match.create({
              data: {
                primaryUserId: mission.ownerUserId,
                secondaryUserId: mission.visitorUserId,
                primaryCircleId: mission.ownerCircleId,
                secondaryCircleId: mission.visitorCircleId,
                type: "match",
                worthItScore: 0.95,
                status: "pending_accept", // Waiting for other user to match
                explanationSummary: "Agent-determined match from interview",
                collisionEventId: `${mission.ownerCircleId}:${mission.visitorCircleId}`,
              },
            });

            logger.info("[AGENT_MATCH] Match created (pending inverse match)", {
              matchId: newMatch.id,
              missionId,
              ownerUserId: mission.ownerUserId,
              visitorUserId: mission.visitorUserId,
            });

            return newMatch;
          }
        });

        // Set longer cooldown for matched users
        logger.debug("[AGENT_MATCH] Setting cooldown for matched users", {
          ownerUserId: mission.ownerUserId,
          visitorUserId: mission.visitorUserId,
        });
        await this.setCooldown(
          mission.ownerUserId,
          mission.visitorUserId,
          "matched",
        );

        const duration = Date.now() - startTime;
        logger.info("[AGENT_MATCH] Match processing completed", {
          matchId: match.id,
          missionId,
          durationMs: duration,
        });
        return toMatch(match);
      }

      // No match from the agent - apply a small deterministic chance
      // of creating a "lucky" match with a generic Spanish explanation.
      if (this.shouldCreateLuckyMatch(mission.id)) {
        const luckyMatch = await prisma.$transaction(async (tx) => {
          // Check for inverse match just like in the regular agent-made flow
          const inverseMatch = await tx.match.findFirst({
            where: {
              OR: [
                {
                  primaryUserId: mission.ownerUserId,
                  secondaryUserId: mission.visitorUserId,
                },
                {
                  primaryUserId: mission.visitorUserId,
                  secondaryUserId: mission.ownerUserId,
                },
              ],
            },
          });

          const genericExplanation =
            "Hubo algo interesante que compartieron; a veces la suerte también conecta a las personas.";

          if (inverseMatch) {
            console.info(
              "Inverse match found - activating both matches (lucky match)",
              {
                missionId,
                existingMatchId: inverseMatch.id,
              },
            );

            // Activate existing inverse match
            await tx.match.update({
              where: { id: inverseMatch.id },
              data: { status: "active" },
            });

            // Create this match as active to keep symmetry
            const newMatch = await tx.match.create({
              data: {
                primaryUserId: mission.ownerUserId,
                secondaryUserId: mission.visitorUserId,
                primaryCircleId: mission.ownerCircleId,
                secondaryCircleId: mission.visitorCircleId,
                type: "match",
                worthItScore: 0.95,
                status: "active",
                explanationSummary: genericExplanation,
                collisionEventId: `${mission.ownerCircleId}:${mission.visitorCircleId}`,
              },
            });

            // Ensure chat exists for the user pair
            const existingChat = await tx.chat.findFirst({
              where: {
                OR: [
                  {
                    primaryUserId: mission.ownerUserId,
                    secondaryUserId: mission.visitorUserId,
                  },
                  {
                    primaryUserId: mission.visitorUserId,
                    secondaryUserId: mission.ownerUserId,
                  },
                ],
              },
            });

            if (!existingChat) {
              await tx.chat.create({
                data: {
                  primaryUserId: mission.ownerUserId,
                  secondaryUserId: mission.visitorUserId,
                },
              });
              console.info("Chat created for lucky mutual match", {
                user1: mission.ownerUserId,
                user2: mission.visitorUserId,
              });
            }

            return newMatch;
          } else {
            // No inverse match yet - create a pending lucky match
            const newMatch = await tx.match.create({
              data: {
                primaryUserId: mission.ownerUserId,
                secondaryUserId: mission.visitorUserId,
                primaryCircleId: mission.ownerCircleId,
                secondaryCircleId: mission.visitorCircleId,
                type: "match",
                worthItScore: 0.95,
                status: "pending_accept",
                explanationSummary: genericExplanation,
                collisionEventId: `${mission.ownerCircleId}:${mission.visitorCircleId}`,
              },
            });

            console.info("Lucky match created (pending inverse match)", {
              matchId: newMatch.id,
              missionId,
            });

            return newMatch;
          }
        });

        // Treat lucky matches like regular matches for cooldown purposes
        await this.setCooldown(
          mission.ownerUserId,
          mission.visitorUserId,
          "matched",
        );

        console.info("Lucky match processing completed", {
          matchId: luckyMatch.id,
          missionId,
        });

        return toMatch(luckyMatch);
      }

      // No match - set cooldown for notification
      logger.info("[AGENT_MATCH] Agent determined no match should be made", {
        missionId,
        ownerUserId: mission.ownerUserId,
        visitorUserId: mission.visitorUserId,
      });
      await this.setCooldown(
        mission.ownerUserId,
        mission.visitorUserId,
        "notified",
      );
      const duration = Date.now() - startTime;
      logger.info("[AGENT_MATCH] Mission completed without match", {
        missionId,
        durationMs: duration,
      });
      return null;
    } catch (error) {
      logger.error("Failed to handle mission result", {
        missionId,
        result,
        error,
      });
      throw error;
    }
  }
}

export const agentMatchService = new AgentMatchService();
