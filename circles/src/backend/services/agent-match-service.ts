import { COLLISION_CONFIG } from '../config/collision.config.js';
import { getRedisClient } from '../infrastructure/redis.js';
import { prisma } from '../lib/prisma.js';
import type { Match } from '../types/match.type.js';

export interface DetectedCollision {
  circle1Id: string;
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
  cooldownType?: 'rejected' | 'matched' | 'notified';
}

/**
 * Service for managing agent-based matching workflow
 * Handles cooldowns, mission creation, and match determination
 */
export class AgentMatchService {
  /**
   * Check if user pair has an active cooldown
   * Cooldowns are tiered based on previous match outcome
   */
  async checkCooldown(
    user1Id: string,
    user2Id: string
  ): Promise<CooldownStatus> {
    try {
      const redis = getRedisClient();
      const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown(user1Id, user2Id);

      const cooldownData = await redis.hgetall(cooldownKey);

      if (!cooldownData || Object.keys(cooldownData).length === 0) {
        // No active cooldown
        return { allowed: true };
      }

      const cooldownTypeValue = cooldownData.type;
      const isValidCooldownType = (
        value: string | undefined
      ): value is 'rejected' | 'matched' | 'notified' => {
        if (value === undefined) {
          return false;
        }
        return value === 'rejected' || value === 'matched' || value === 'notified';
      };
      const cooldownType: 'rejected' | 'matched' | 'notified' | undefined = isValidCooldownType(
        cooldownTypeValue
      )
        ? cooldownTypeValue
        : undefined;

      const expiresAt = parseInt(cooldownData.expiresAt || '0');
      const now = Date.now();

      if (now > expiresAt) {
        // Cooldown has expired
        await redis.del(cooldownKey);
        return { allowed: true };
      }

      const remainingMs = expiresAt - now;
      return {
        allowed: false,
        reason: `Cooldown active (${cooldownType || 'unknown'})`,
        remainingMs,
        cooldownType: cooldownType || 'notified',
      };
    } catch (error) {
      console.error('Failed to check cooldown', { error });
      // In case of error, allow the match to proceed (fail open)
      return { allowed: true };
    }
  }

  /**
   * Create mission for a detected collision
   * Acquires distributed lock to prevent duplicate missions
   */
  async createMissionForCollision(
    collision: DetectedCollision
  ): Promise<Awaited<ReturnType<typeof prisma.interviewMission.create>> | null> {
    const lockKey = COLLISION_CONFIG.REDIS_KEYS.inFlightMission(
      collision.circle1Id,
      collision.circle2Id
    );
    const redis = getRedisClient();
    const workerId = `worker-${Date.now()}-${Math.random()}`;

    try {
      // Acquire distributed lock (NX = only if not exists, EX = auto-expire)
      const lockAcquired = await redis.set(
        lockKey,
        workerId,
        'EX',
        COLLISION_CONFIG.IN_FLIGHT_MISSION_TTL,
        'NX'
      );

      if (!lockAcquired) {
        console.debug('Mission creation already in progress for collision', {
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
        });
        return null;
      }

      // Check cooldown one more time before creating mission
      const cooldownCheck = await this.checkCooldown(
        collision.user1Id,
        collision.user2Id
      );

      if (!cooldownCheck.allowed) {
        console.debug('Cooldown active, skipping mission creation', {
          collision,
          cooldown: cooldownCheck,
        });
        await redis.del(lockKey);
        return null;
      }

      // Create interview mission in database
      const mission = await prisma.interviewMission.create({
        data: {
          ownerUserId: collision.user1Id,
          visitorUserId: collision.user2Id,
          ownerCircleId: collision.circle1Id,
          visitorCircleId: collision.circle2Id,
          collisionEventId: `${collision.circle1Id}:${collision.circle2Id}`, // Unique key for the collision
          status: 'pending',
          attemptNumber: 1,
        },
      });

      // Update collision event with mission reference
      await prisma.collisionEvent.update({
        where: {
          unique_collision_pair: {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
          },
        },
        data: {
          missionId: mission.id,
          status: 'mission_created',
        },
      });

      console.info('Mission created for collision', {
        missionId: mission.id,
        collision,
      });

      return mission;
    } catch (error) {
      console.error('Failed to create mission for collision', { collision, error });
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
    outcome: 'rejected' | 'matched' | 'notified'
  ): Promise<void> {
    try {
      const redis = getRedisClient();
      const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown(user1Id, user2Id);

      // Determine cooldown duration based on outcome
      let cooldownDurationMs: number;
      switch (outcome) {
        case 'rejected':
          cooldownDurationMs = COLLISION_CONFIG.COOLDOWN_DURATIONS.rejected;
          break;
        case 'matched':
          cooldownDurationMs = COLLISION_CONFIG.COOLDOWN_DURATIONS.matched;
          break;
        case 'notified':
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

      console.info('Cooldown set for user pair', {
        user1Id,
        user2Id,
        outcome,
        expiresAt,
        durationMs: cooldownDurationMs,
      });
    } catch (error) {
      console.error('Failed to set cooldown', { user1Id, user2Id, outcome, error });
      // Don't throw - cooldown failure shouldn't block the system
    }
  }

  /**
   * Handle mission result and create match if successful
   * Called by mission worker after agent completes interview
   */
  async handleMissionResult(missionId: string, result: MissionResult): Promise<Match | null> {
    try {
      // Fetch the mission
      const mission = await prisma.interviewMission.findUnique({
        where: { id: missionId },
      });

      if (!mission) {
        console.warn('Mission not found for result handling', { missionId });
        return null;
      }

      // Update mission status
      await prisma.interviewMission.update({
        where: { id: missionId },
        data: {
          status: result.success ? 'completed' : 'failed',
          transcript: result.transcript
            ? (typeof result.transcript === 'string' ? JSON.parse(result.transcript) : result.transcript)
            : undefined,
          judgeDecision: result.judgeDecision ?? null,
          failureReason: result.error || null,
          completedAt: new Date(),
        },
      });

      if (!result.success) {
        console.info('Mission failed', { missionId, error: result.error });
        // Set cooldown for failed mission (notified outcome)
        await this.setCooldown(mission.ownerUserId, mission.visitorUserId, 'notified');
        return null;
      }

      // If match was made by agent, create Match record
      if (result.matchMade) {
        const match = await prisma.match.create({
          data: {
            primaryUserId: mission.ownerUserId,
            secondaryUserId: mission.visitorUserId,
            primaryCircleId: mission.ownerCircleId,
            secondaryCircleId: mission.visitorCircleId,
            type: 'match',
            worthItScore: 0.95, // High score for agent-matched users
            status: 'pending_accept',
            explanationSummary: 'Agent-determined match from interview',
            collisionEventId: `${mission.ownerCircleId}:${mission.visitorCircleId}`,
          },
        });

        // Set longer cooldown for matched users
        await this.setCooldown(mission.ownerUserId, mission.visitorUserId, 'matched');

        console.info('Match created from mission result', { matchId: match.id, missionId });
        return match;
      }

      // No match - set cooldown for notification
      await this.setCooldown(mission.ownerUserId, mission.visitorUserId, 'notified');
      console.info('Mission completed without match', { missionId });
      return null;
    } catch (error) {
      console.error('Failed to handle mission result', { missionId, result, error });
      throw error;
    }
  }

}

export const agentMatchService = new AgentMatchService();
