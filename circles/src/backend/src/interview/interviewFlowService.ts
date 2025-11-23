import type { InterviewAgentsRuntime } from './agentsRuntime.js';
import type { InterviewJudge } from './judge.js';
import type { NotificationGateway } from './notificationGateway.js';
import { redactAgentMessage } from './piiFilter.js';
import type {
  InterviewFlowConfig,
  InterviewMission,
  InterviewMissionResult,
  OwnerTurnGoal,
  TranscriptMessage
} from './types.js';
import { agentMatchService } from '../../services/agent-match-service.js';
import { logger } from '../../utils/logger.util.js';

const defaultConfig: InterviewFlowConfig = {
  max_owner_turns: 3
};

export interface IInterviewFlowService {
  runMission(mission: InterviewMission): Promise<InterviewMissionResult>;
}

export class InterviewFlowService implements IInterviewFlowService {
  private readonly agentsRuntime: InterviewAgentsRuntime;
  private readonly judge: InterviewJudge;
  private readonly notificationGateway: NotificationGateway;
  private readonly config: InterviewFlowConfig;

  constructor(options: {
    agentsRuntime: InterviewAgentsRuntime;
    judge: InterviewJudge;
    notificationGateway: NotificationGateway;
    config?: Partial<InterviewFlowConfig>;
  }) {
    this.agentsRuntime = options.agentsRuntime;
    this.judge = options.judge;
    this.notificationGateway = options.notificationGateway;
    this.config = { ...defaultConfig, ...options.config };
  }

  async runMission(mission: InterviewMission): Promise<InterviewMissionResult> {
    const transcript: TranscriptMessage[] = [];

    let ownerTurnCount = 0;
    let shouldStop = false;

    logger.info(
      `Starting interview mission ${mission.mission_id} (owner=${mission.owner_user_id}, visitor=${mission.visitor_user_id})`
    );

    while (!shouldStop && ownerTurnCount < this.config.max_owner_turns) {
      const ownerGoal = this.pickOwnerTurnGoal(ownerTurnCount);

      const ownerTurn = await this.agentsRuntime.runOwnerTurn({
        owner_profile: mission.owner_profile,
        visitor_profile: mission.visitor_profile,
        owner_circle: mission.owner_circle,
        context: mission.context,
        conversation_so_far: transcript,
        turn_goal: ownerGoal
      });

      const ownerMessageRedacted = redactAgentMessage(
        ownerTurn.as_user_message,
        mission.owner_profile
      );

      transcript.push({
        speaker: 'owner',
        message: ownerMessageRedacted
      });

      logger.info(
        [
          '',
          `Mission ${mission.mission_id} – owner turn ${ownerTurnCount} (${ownerGoal})`,
          `\t[OWNER] ${ownerMessageRedacted}`
        ].join('\n')
      );

      ownerTurnCount += 1;
      shouldStop = ownerTurn.stop_suggested === true;

      if (shouldStop) {
        break;
      }

      const visitorTurn = await this.agentsRuntime.runVisitorTurn({
        visitor_profile: mission.visitor_profile,
        owner_profile: mission.owner_profile,
        context: mission.context,
        conversation_so_far: transcript
      });

      const visitorMessageRedacted = redactAgentMessage(
        visitorTurn.as_user_message,
        mission.visitor_profile
      );

      transcript.push({
        speaker: 'visitor',
        message: visitorMessageRedacted
      });

      logger.info(
        [
          '',
          `Mission ${mission.mission_id} – visitor turn ${ownerTurnCount}`,
          `\t[VISITOR] ${visitorMessageRedacted}`,
          ''
        ].join('\n')
      );

      if (visitorTurn.stop_suggested === true) {
        break;
      }
    }

    const judgeDecision = await this.judge.evaluate({
      owner_objective: mission.owner_circle.objective_text,
      transcript
    });

    if (judgeDecision.should_notify) {
      const notificationTurn = await this.agentsRuntime.runOwnerTurn({
        owner_profile: mission.owner_profile,
        visitor_profile: mission.visitor_profile,
        owner_circle: mission.owner_circle,
        context: mission.context,
        conversation_so_far: transcript,
        turn_goal: 'notify_user'
      });

      const notificationTextRaw = notificationTurn.as_user_message.trim();

      const notificationTextRedacted = redactAgentMessage(
        notificationTextRaw,
        mission.visitor_profile
      );

      if (notificationTextRedacted.length > 0) {
        judgeDecision.notification_text = notificationTextRedacted;
      }
    }

    logger.info(
      `Mission ${mission.mission_id} – judge decision: should_notify=${judgeDecision.should_notify}${
        judgeDecision.notification_text ? `, notification="${judgeDecision.notification_text}"` : ''
      }`
    );

    if (judgeDecision.should_notify && judgeDecision.notification_text) {
      await this.notificationGateway.notifySuccessfulInteraction({
        mission_id: mission.mission_id,
        owner_user_id: mission.owner_user_id,
        visitor_user_id: mission.visitor_user_id,
        notification_text: judgeDecision.notification_text
      });
    }

    // Call agent match service to handle mission result and create match if needed
    try {
      await agentMatchService.handleMissionResult(mission.mission_id, {
        success: true,
        matchMade: judgeDecision.should_notify,
        transcript: JSON.stringify(transcript),
        judgeDecision: judgeDecision
      });
      logger.info(`Mission ${mission.mission_id} result processed successfully`);
    } catch (error) {
      logger.error(`Failed to process mission ${mission.mission_id} result`, error);
      // Don't throw - mission completed successfully, match creation failure is a separate concern
    }

    return {
      mission_id: mission.mission_id,
      transcript,
      judge_decision: judgeDecision
    };
  }

  private pickOwnerTurnGoal(turnIndex: number): OwnerTurnGoal {
    if (turnIndex === 0) {
      return 'open_and_ask_one_focused_question';
    }

    if (turnIndex === 1) {
      return 'clarify_objective';
    }

    if (turnIndex === 2) {
      return 'clarify_availability';
    }

    return 'decide_and_close';
  }
}
