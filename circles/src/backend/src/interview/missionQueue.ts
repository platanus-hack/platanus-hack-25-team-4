import { Queue, type JobsOptions } from 'bullmq';
import { Redis } from 'ioredis';

import type { InterviewMission } from './types.js';
import { env } from '../../config/env.js';
import { logger } from '../../utils/logger.util.js';

const connection = new Redis(env.redisUrl, {
  // BullMQ requires maxRetriesPerRequest to be null when using blocking commands.
  maxRetriesPerRequest: null
});

export const missionQueue = new Queue<InterviewMission>(env.missionQueueName, {
  connection
});

export const enqueueMission = async (
  mission: InterviewMission,
  options?: JobsOptions
): Promise<string> => {
  const job = await missionQueue.add(mission.mission_id, mission, {
    removeOnComplete: true,
    removeOnFail: false,
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000
    },
    ...options
  });

  logger.info(
    `Enqueued interview mission ${mission.mission_id} as job ${String(job.id)} on queue ${env.missionQueueName}`
  );

  return String(job.id);
};


