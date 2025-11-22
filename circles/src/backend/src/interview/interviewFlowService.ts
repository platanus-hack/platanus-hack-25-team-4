import type {
  InterviewFlowConfig,
  InterviewMission,
  InterviewMissionResult,
  OwnerTurnGoal,
  TranscriptMessage
} from './types.js';
import type { InterviewAgentsRuntime } from './agentsRuntime.js';
import type { InterviewJudge } from './judge.js';
import type { NotificationGateway } from './notificationGateway.js';

const defaultConfig: InterviewFlowConfig = {
  max_owner_turns: 3
};

export class InterviewFlowService {
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

      transcript.push({
        speaker: 'owner',
        message: ownerTurn.as_user_message
      });

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

      transcript.push({
        speaker: 'visitor',
        message: visitorTurn.as_user_message
      });

      if (visitorTurn.stop_suggested === true) {
        break;
      }
    }

    const judgeDecision = await this.judge.evaluate({
      owner_objective: mission.owner_circle.objective_text,
      transcript
    });

    if (judgeDecision.should_notify && judgeDecision.notification_text) {
      await this.notificationGateway.notifySuccessfulInteraction({
        mission_id: mission.mission_id,
        owner_user_id: mission.owner_user_id,
        visitor_user_id: mission.visitor_user_id,
        notification_text: judgeDecision.notification_text
      });
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

