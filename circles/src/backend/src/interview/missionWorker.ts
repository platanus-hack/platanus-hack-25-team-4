import { BedrockInterviewAgentsRuntime } from './agentsRuntime.js';
import { InterviewFlowService, type IInterviewFlowService } from './interviewFlowService.js';
import { BedrockInterviewJudge } from './judge.js';
import { LoggingNotificationGateway } from './notificationGateway.js';
import { InterviewMission } from './types.js';

export interface MissionJob {
  id: string;
  data: InterviewMission;
}

export interface MissionJobHandler {
  (job: MissionJob): Promise<void>;
}

export const createMissionJobHandler = (
  flowService: IInterviewFlowService
): MissionJobHandler => {
  return async (job: MissionJob): Promise<void> => {
    await flowService.runMission(job.data);
  };
};

export const createDefaultMissionJobHandler = (): MissionJobHandler => {
  const flowService = new InterviewFlowService({
    agentsRuntime: new BedrockInterviewAgentsRuntime(),
    judge: new BedrockInterviewJudge(),
    notificationGateway: new LoggingNotificationGateway()
  });

  return createMissionJobHandler(flowService);
};

