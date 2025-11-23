import { prisma } from '../lib/prisma.js';
import { AgentMatchService, MissionResult } from '../services/agent-match-service.js';

type InterviewMission = Awaited<ReturnType<typeof prisma.interviewMission.findMany>>[number];

/**
 * Mission Worker
 *
 * Processes interview missions and handles results from the interview flow.
 * This worker integrates with the agent-based interview system to:
 * 1. Execute interviews for pending missions
 * 2. Process interview results
 * 3. Create matches based on interview outcomes
 * 4. Update cooldowns based on match results
 */
export class MissionWorker {
  private agentMatchService: AgentMatchService;
  private isRunning = false;
  private concurrency = 3; // Process up to 3 missions in parallel

  constructor(concurrency: number = 3) {
    this.agentMatchService = new AgentMatchService();
    this.concurrency = concurrency;
  }

  /**
   * Start the mission worker (runs every 10 seconds)
   */
  start(intervalMs: number = 10000): void {
    if (this.isRunning) {
      console.warn('Mission worker is already running');
      return;
    }

    this.isRunning = true;
    console.info('Starting mission worker with concurrency', {
      intervalMs,
      concurrency: this.concurrency
    });

    // Run immediately on start
    this.tick().catch(error => {
      console.error('Mission worker error on initial tick', { error });
    });

    // Then run at intervals
    setInterval(
      () => {
        this.tick().catch(error => {
          console.error('Mission worker error', { error });
        });
      },
      intervalMs
    );
  }

  /**
   * Main tick function - fetch and process pending missions
   */
  private async tick(): Promise<void> {
    try {
      // Get pending missions
      const pendingMissions = await prisma.interviewMission.findMany({
        where: {
          status: 'pending'
        },
        take: this.concurrency,
        orderBy: {
          createdAt: 'asc'
        }
      });

      if (pendingMissions.length === 0) {
        return;
      }

      console.debug('Mission worker processing missions', {
        count: pendingMissions.length
      });

      // Process missions in parallel (up to concurrency limit)
      await Promise.all(
        pendingMissions.map((mission: InterviewMission) => this.processMission(mission))
      );

    } catch (error) {
      console.error('Mission worker tick failed', { error });
    }
  }

  /**
   * Process a single mission
   * In a real implementation, this would call the interview flow service
   */
  private async processMission(mission: InterviewMission): Promise<void> {
    try {
      // Update mission status to in_progress
      await prisma.interviewMission.update({
        where: { id: mission.id },
        data: {
          status: 'in_progress',
          startedAt: new Date()
        }
      });

      console.info('Processing mission', {
        missionId: mission.id,
        ownerUserId: mission.ownerUserId,
        visitorUserId: mission.visitorUserId
      });

      // TODO: Call interview flow service here
      // const interviewResult = await interviewFlowService.conductInterview(mission);

      // For now, simulate a successful interview with no match
      // In production, this would be the actual interview flow result
      const simulatedResult = {
        success: true,
        matchMade: false,
        transcript: JSON.stringify({
          messages: [
            {
              role: 'interviewer',
              content: 'Interview conducted successfully'
            }
          ]
        }),
        judgeDecision: {
          reason: 'Simulated interview - awaiting real interview flow integration',
          confidence: 0
        }
      };

      // Handle mission result through AgentMatchService
      await this.agentMatchService.handleMissionResult(mission.id, simulatedResult);

      console.info('Mission processed successfully', {
        missionId: mission.id,
        matchMade: simulatedResult.matchMade
      });

    } catch (error) {
      // Handle mission processing failure
      console.error('Failed to process mission', {
        missionId: mission.id,
        error
      });

      // Mark mission as failed after max retries
      const maxRetries = 3;
      if (mission.attemptNumber >= maxRetries) {
        await prisma.interviewMission.update({
          where: { id: mission.id },
          data: {
            status: 'failed',
            failureReason: error instanceof Error ? error.message : 'Unknown error',
            completedAt: new Date()
          }
        });

        // Set cooldown for failed mission
        await this.agentMatchService.setCooldown(
          mission.ownerUserId,
          mission.visitorUserId,
          'notified'
        );
      } else {
        // Retry mission
        await prisma.interviewMission.update({
          where: { id: mission.id },
          data: {
            status: 'pending',
            attemptNumber: mission.attemptNumber + 1
          }
        });
      }
    }
  }

  /**
   * Handle mission result - called by interview flow when interview completes
   * This is the integration point for external interview systems
   */
  async handleMissionResult(
    missionId: string,
    result: MissionResult
  ): Promise<void> {
    try {
      // Delegate to AgentMatchService
      await this.agentMatchService.handleMissionResult(missionId, result);

      console.info('Mission result handled', {
        missionId,
        success: result.success,
        matchMade: result.matchMade
      });
    } catch (error) {
      console.error('Failed to handle mission result', {
        missionId,
        error
      });
      throw error;
    }
  }

  /**
   * Gracefully stop the worker
   */
  stop(): void {
    this.isRunning = false;
    console.info('Mission worker stopped');
  }
}

// Export singleton instance
export const missionWorker = new MissionWorker();
