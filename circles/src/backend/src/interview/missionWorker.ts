import type { InterviewMission } from './types.js';
import { InterviewFlowService } from './interviewFlowService.js';
import { MockInterviewAgentsRuntime } from './agentsRuntime.js';
import { MockInterviewJudge } from './judge.js';
import { LoggingNotificationGateway } from './notificationGateway.js';

export interface MissionJob {
  id: string;
  data: InterviewMission;
}

export interface MissionJobHandler {
  (job: MissionJob): Promise<void>;
}

export const createMissionJobHandler = (
  flowService: InterviewFlowService
): MissionJobHandler => {
  return async (job: MissionJob): Promise<void> => {
    await flowService.runMission(job.data);
  };
};

export const createDefaultMissionJobHandler = (): MissionJobHandler => {
  const flowService = new InterviewFlowService({
    agentsRuntime: new MockInterviewAgentsRuntime(),
    judge: new MockInterviewJudge(),
    notificationGateway: new LoggingNotificationGateway()
  });

  return createMissionJobHandler(flowService);
};

