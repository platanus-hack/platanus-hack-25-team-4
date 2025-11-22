import type { JudgeDecision, JudgeInput } from './types.js';

export interface InterviewJudge {
  evaluate(input: JudgeInput): Promise<JudgeDecision>;
}

export class MockInterviewJudge implements InterviewJudge {
  async evaluate(input: JudgeInput): Promise<JudgeDecision> {
    const { owner_objective, transcript } = input;

    const fullConversation = transcript.map((turn) => turn.message).join('\n');

    const containsConcreteSignal =
      fullConversation.toLowerCase().includes('meet') ||
      fullConversation.toLowerCase().includes('coffee') ||
      fullConversation.toLowerCase().includes('let\'s') ||
      fullConversation.toLowerCase().includes('lets');

    if (!containsConcreteSignal) {
      return {
        should_notify: false
      };
    }

    const notification_text = `Looks like this could help with: “${owner_objective}”. Want to connect?`;

    return {
      should_notify: true,
      notification_text
    };
  }
}

