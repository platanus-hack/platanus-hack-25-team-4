import { COLLISION_CONFIG } from "../config/collision.config.js";
import { getRedisClient } from "../infrastructure/redis.js";
import { prisma } from "../lib/prisma.js";
import { enqueueMission } from "../src/interview/missionQueue.js";
import type { InterviewMission } from "../src/interview/types.js";
import { MatchType, MatchStatus } from "../types/index.js";
import type { Match } from "../types/match.type.js";
import type { UserProfile } from "../types/user.type.js";


export interface DetectedCollision {
  circle1Id: string | null; // Null when visitor doesn't have a circle
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distance: number;
  timestamp: number;
}

export interface MissionResult {
  success: boolean;
  matchMade: boolean;
  transcript?: string;
  judgeDecision?: unknown;
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
      console.error("Failed to check inverse match", {
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
      const redis = getRedisClient();
      const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown(
        user1Id,
        user2Id,
      );

      const cooldownData = await redis.hgetall(cooldownKey);

      if (!cooldownData || Object.keys(cooldownData).length === 0) {
        // No active cooldown
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
        await redis.del(cooldownKey);
        return { allowed: true };
      }

      const remainingMs = expiresAt - now;
      return {
        allowed: false,
        reason: `Cooldown active (${cooldownType || "unknown"})`,
        remainingMs,
        cooldownType: cooldownType || "notified",
      };
    } catch (error) {
      console.error("Failed to check cooldown", { error });
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
    // Generate lock key - use user1Id if circle1Id is null
    const lockIdentifier = collision.circle1Id || collision.user1Id;
    const lockKey = COLLISION_CONFIG.REDIS_KEYS.inFlightMission(
      lockIdentifier,
      collision.circle2Id,
    );
    const redis = getRedisClient();
    const workerId = `worker-${Date.now()}-${Math.random()}`;

    try {
      // Acquire distributed lock (NX = only if not exists, EX = auto-expire)
      const lockAcquired = await redis.set(
        lockKey,
        workerId,
        "EX",
        COLLISION_CONFIG.IN_FLIGHT_MISSION_TTL,
        "NX",
      );

      if (!lockAcquired) {
        console.debug("Mission creation already in progress for collision", {
          lockIdentifier,
          circle2Id: collision.circle2Id,
        });
        return null;
      }

      // Check cooldown one more time before creating mission
      const cooldownCheck = await this.checkCooldown(
        collision.user1Id,
        collision.user2Id,
      );

      if (!cooldownCheck.allowed) {
        console.debug("Cooldown active, skipping mission creation", {
          collision,
          cooldown: cooldownCheck,
        });
        await redis.del(lockKey);
        return null;
      }

      // For missions, we need both users to have circles
      // If visitor (user1) doesn't have a circle, we need to find or create one
      let ownerCircleId = collision.circle1Id;
      if (!ownerCircleId) {
        // Get the visitor's first active circle, or skip mission creation
        const visitorCircle = await prisma.circle.findFirst({
          where: {
            userId: collision.user1Id,
            status: "active",
            expiresAt: { gt: new Date() },
          },
        });

        if (!visitorCircle) {
          console.warn(
            "Visitor has no active circles, skipping mission creation",
            {
              userId: collision.user1Id,
            },
          );
          await redis.del(lockKey);
          return null;
        }
        ownerCircleId = visitorCircle.id;
      }

      // Create collision event ID
      const collisionEventId = `${lockIdentifier}:${collision.circle2Id}`;

      // Create interview mission in database
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

      // Try to update collision event if it exists
      try {
        if (collision.circle1Id) {
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
        }
      } catch (error) {
        // CollisionEvent might not exist if circle1Id was null
        console.debug("CollisionEvent not found or could not be updated", {
          error,
        });
      }

      console.info("Mission created for collision", {
        missionId: mission.id,
        collision,
      });

      // Enqueue the mission for processing by the interview worker
      try {
        const missionPayload = await this.prepareMissionPayload(mission);
        await enqueueMission(missionPayload);
        console.info("Mission enqueued for interview processing", {
          missionId: mission.id,
        });
      } catch (error) {
        console.error("Failed to enqueue mission", {
          missionId: mission.id,
          error,
        });
        // Don't throw - mission is created, worker can pick it up later
      }

      return mission;
    } catch (error) {
      console.error("Failed to create mission for collision", {
        collision,
        error,
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

      await redis.hset(cooldownKey, {
        type: outcome,
        expiresAt: String(expiresAt),
        createdAt: String(Date.now()),
      });

      // Set TTL on the key itself (safety measure)
      await redis.expire(cooldownKey, Math.ceil(cooldownDurationMs / 1000));

      console.info("Cooldown set for user pair", {
        user1Id,
        user2Id,
        outcome,
        expiresAt,
        durationMs: cooldownDurationMs,
      });
    } catch (error) {
      console.error("Failed to set cooldown", {
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
    try {
      // Fetch the mission
      const mission = await prisma.interviewMission.findUnique({
        where: { id: missionId },
      });

      if (!mission) {
        console.warn("Mission not found for result handling", { missionId });
        return null;
      }

      // Update mission status
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

      if (!result.success) {
        console.info("Mission failed", { missionId, error: result.error });
        // Set cooldown for failed mission (notified outcome)
        await this.setCooldown(
          mission.ownerUserId,
          mission.visitorUserId,
          "notified",
        );
        return null;
      }

      // If match was made by agent, check for inverse match first
      if (result.matchMade) {
        // Use transaction to prevent race conditions
        const match = await prisma.$transaction(async (tx) => {
          // Check if inverse match already exists
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
            console.info("Inverse match found - activating both matches", {
              missionId,
              existingMatchId: inverseMatch.id,
            });

            // Update the existing match to 'active'
            await tx.match.update({
              where: { id: inverseMatch.id },
              data: { status: "active" },
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
              await tx.chat.create({
                data: {
                  primaryUserId: mission.ownerUserId,
                  secondaryUserId: mission.visitorUserId,
                },
              });
              console.info("Chat created for mutual match", {
                user1: mission.ownerUserId,
                user2: mission.visitorUserId,
              });
            }

            return newMatch;
          } else {
            // No inverse match - create pending match
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

            console.info("Match created (pending inverse match)", {
              matchId: newMatch.id,
              missionId,
            });

            return newMatch;
          }
        });

        // Set longer cooldown for matched users
        await this.setCooldown(
          mission.ownerUserId,
          mission.visitorUserId,
          "matched",
        );

        console.info("Match processing completed", {
          matchId: match.id,
          missionId,
        });

        return toMatch(match);
      }

      // No match - set cooldown for notification
      await this.setCooldown(
        mission.ownerUserId,
        mission.visitorUserId,
        "notified",
      );
      console.info("Mission completed without match", { missionId });
      return null;
    } catch (error) {
      console.error("Failed to handle mission result", {
        missionId,
        result,
        error,
      });
      throw error;
    }
  }
}

export const agentMatchService = new AgentMatchService();
