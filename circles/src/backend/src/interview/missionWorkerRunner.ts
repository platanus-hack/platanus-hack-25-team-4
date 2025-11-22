import { QueueEvents, Worker, type Job } from 'bullmq';
import { Redis } from 'ioredis';

import { createDefaultMissionJobHandler } from './missionWorker.js';
import type { InterviewMission } from './types.js';
import { env } from '../../config/env.js';
import { logger } from '../../utils/logger.util.js';

const createConnection = () => {
  return new Redis(env.redisUrl, {
    // BullMQ requires maxRetriesPerRequest to be null when using blocking commands.
    maxRetriesPerRequest: null
  });
};

const startWorker = (): void => {
  const connection = createConnection();

  const missionJobHandler = createDefaultMissionJobHandler();

  const worker = new Worker<InterviewMission>(
    env.missionQueueName,
    async (bullJob: Job<InterviewMission>): Promise<void> => {
      const mission = bullJob.data;

      const missionId = mission.mission_id;
      const jobId = String(bullJob.id ?? missionId);

      logger.info(
        `Mission worker picked up job ${jobId} for mission ${missionId}`
      );

      await missionJobHandler({
        id: jobId,
        data: mission
      });
    },
    {
      connection,
      concurrency: env.missionWorkerConcurrency
    }
  );

  worker.on('completed', (job: Job<InterviewMission>) => {
    const data = job.data;
    logger.info(
      `Mission job ${String(job.id)} for mission ${data.mission_id} completed`
    );
  });

  worker.on(
    'failed',
    (job: Job<InterviewMission> | undefined, err: Error, _prev: string) => {
      const missionId = job?.data.mission_id ?? 'unknown';

      logger.error(
        `Mission job ${String(job?.id ?? 'unknown')} for mission ${missionId} failed: ${
          err?.message ?? 'unknown error'
        }`
      );
    }
  );

  const queueEvents = new QueueEvents(env.missionQueueName, {
    connection: createConnection()
  });

  queueEvents.on(
    'stalled',
    (event: { jobId: string | undefined; prev?: string | undefined }) => {
      logger.warn(`Mission job ${event.jobId} stalled`);
    }
  );

  logger.info(
    `Mission worker started for queue "${env.missionQueueName}" with concurrency ${env.missionWorkerConcurrency}`
  );
};

void (async () => {
  startWorker();
})();


