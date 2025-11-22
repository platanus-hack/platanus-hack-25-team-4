import type {
  AgentTurnOutput,
  OwnerTurnInput,
  VisitorTurnInput
} from './types.js';

export interface InterviewAgentsRuntime {
  runOwnerTurn(input: OwnerTurnInput): Promise<AgentTurnOutput>;
  runVisitorTurn(input: VisitorTurnInput): Promise<AgentTurnOutput>;
}

export class MockInterviewAgentsRuntime implements InterviewAgentsRuntime {
  async runOwnerTurn(input: OwnerTurnInput): Promise<AgentTurnOutput> {
    const { owner_profile, visitor_profile, owner_circle, conversation_so_far, turn_goal } = input;

    if (conversation_so_far.length === 0 && owner_profile.conversation_micro_preferences?.preferred_opener_style) {
      return {
        as_user_message: owner_profile.conversation_micro_preferences.preferred_opener_style,
        intent_tag: 'clarify_goal',
        stop_suggested: false
      };
    }

    switch (turn_goal) {
      case 'open_and_ask_one_focused_question': {
        return {
          as_user_message: `Hey ${visitor_profile.display_name}, I have a circle running for “${owner_circle.objective_text}”. Would this fit your week at all?`,
          intent_tag: 'clarify_goal',
          stop_suggested: false
        };
      }
      case 'clarify_objective': {
        return {
          as_user_message: `From what you shared, it sounds like we might align with my goal: ${owner_profile.motivations_and_goals.primary_goal}. Could you share briefly what you are looking for right now?`,
          intent_tag: 'clarify_goal',
          stop_suggested: false
        };
      }
      case 'clarify_availability': {
        return {
          as_user_message: `If this seems interesting, when around ${owner_circle.time_window} would you realistically be free within ~${owner_circle.radius_m}m?`,
          intent_tag: 'clarify_time',
          stop_suggested: false
        };
      }
      case 'decide_and_close': {
        const ownerName = owner_profile.display_name;
        return {
          as_user_message: `Thanks for the chat! Based on what you said, I think it could be worth a quick meetup if you are up for it. Otherwise, no worries at all 🙂\n\n– ${ownerName}`,
          intent_tag: 'propose_meet',
          stop_suggested: true
        };
      }
      default: {
        return {
          as_user_message: `Thanks for the chat!`,
          stop_suggested: true
        };
      }
    }
  }

  async runVisitorTurn(input: VisitorTurnInput): Promise<AgentTurnOutput> {
    const { visitor_profile, owner_profile, context, conversation_so_far } = input;

    const lastOwnerMessage = [...conversation_so_far]
      .reverse()
      .find((message) => message.speaker === 'owner');

    const baseReply = lastOwnerMessage
      ? `Hey ${owner_profile.display_name}, thanks for reaching out about “${lastOwnerMessage.message.slice(0, 80)}...”`
      : `Hey ${owner_profile.display_name}, nice to meet you here.`;

    const goalSnippet = visitor_profile.motivations_and_goals.primary_goal;

    const timeHint =
      context.approximate_distance_m <= 1000
        ? 'I am pretty close by, so short-notice plans could work.'
        : 'I am a bit further away, but still open if we find a good time.';

    return {
      as_user_message: `${baseReply}\n\nI am mostly looking for: ${goalSnippet}.\n${timeHint}`,
      intent_tag: 'clarify_goal',
      stop_suggested: false
    };
  }
}

