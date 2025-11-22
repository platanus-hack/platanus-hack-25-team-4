import { generateClaudeText } from './anthropicClient.js';
import { generateLlama4ScoutText } from './bedrockLlamaClient.js';
import type { AgentTurnOutput, OwnerTurnInput, VisitorTurnInput } from './types.js';

export interface InterviewAgentsRuntime {
  runOwnerTurn(input: OwnerTurnInput): Promise<AgentTurnOutput>;
  runVisitorTurn(input: VisitorTurnInput): Promise<AgentTurnOutput>;
}

const describeOwnerTurnGoal = (turnGoal: OwnerTurnInput['turn_goal']): string => {
  if (turnGoal === 'open_and_ask_one_focused_question') {
    return 'Open the conversation naturally and ask one focused question that helps you see if this visitor could fit your circle objective. Do not propose any concrete plans or real-world actions.';
  }

  if (turnGoal === 'clarify_objective') {
    return 'Clarify in simple, human terms what you are looking for and check if the visitor is aligned, without oversharing personal details. Do not make or accept specific plans; focus on understanding fit.';
  }

  if (turnGoal === 'clarify_availability') {
    return 'Clarify the visitor’s general availability and constraints (for example, days or time of day) without proposing specific times, places, or concrete plans.';
  }

  if (turnGoal === 'notify_user') {
    return 'After the whole conversation, you now need to write a short push notification message to your human user (the circle owner) explaining that this interaction looks promising and asking if they would like to take the opportunity to connect. Speak directly to your user in second person, as their agent, and focus on how this could help with their circle objective.';
  }

  return 'Summarize what you have learned about the visitor and decide whether it seems promising enough that the humans might want to connect later. Wrap up politely without proposing or agreeing to any specific times, places, or real-world actions.';
};

const formatConversationHistory = (conversation: OwnerTurnInput['conversation_so_far']): string => {
  if (conversation.length === 0) {
    return 'No previous messages. You are writing the first one.';
  }

  const lines = conversation.map((turn) => {
    const speakerLabel = turn.speaker === 'owner' ? 'Owner' : 'Visitor';
    return `${speakerLabel}: ${turn.message}`;
  });

  return lines.join('\n');
};

export class BedrockInterviewAgentsRuntime implements InterviewAgentsRuntime {
  async runOwnerTurn(input: OwnerTurnInput): Promise<AgentTurnOutput> {
    const { owner_profile, visitor_profile, owner_circle, context, conversation_so_far, turn_goal } =
      input;

    if (turn_goal === 'notify_user') {
      const conversationText = formatConversationHistory(conversation_so_far);

      const prompt = [
        'You are the agent persona for the circle OWNER in a location-based social app.',
        'You are about to talk to your own human user (the circle owner), not to the visitor.',
        '',
        `Owner display name: ${owner_profile.display_name}`,
        `Owner primary goal: ${owner_profile.motivations_and_goals.primary_goal}`,
        '',
        `Visitor display name: ${visitor_profile.display_name}`,
        `Visitor primary goal: ${visitor_profile.motivations_and_goals.primary_goal}`,
        '',
        `Circle objective: ${owner_circle.objective_text}`,
        `Circle time window: ${owner_circle.time_window}`,
        `Approximate distance between owner and visitor: ${context.approximate_distance_m} meters`,
        '',
        'Conversation transcript between owner and visitor:',
        conversationText,
        '',
        'Task:',
        'Write a single push-notification style sentence to your human user in their language, from the perspective of their own agent.',
        'Explain briefly why this visitor seems like a good opportunity that could help with the owner’s objective, and ask if they would like to take it (for example, to chat or meet).',
        '',
        'Constraints:',
        '- Address the user directly in second person (e.g., "¿Te interesaría...?", "Would you like...").',
        '- Keep it short and clear, as a single push notification line.',
        '- Do not mention the app or that you are an agent; sound like their own inner voice / assistant.',
        '- Do not include any full names, email addresses, phone numbers, or social handles.',
        '- Focus on the opportunity (who the other person is and why it fits the objective) and on asking for their confirmation.',
        '- Return ONLY the notification text, nothing else.'
      ]
        .filter((part) => part.length > 0)
        .join('\n');

      const generation = await generateLlama4ScoutText(prompt);
      const trimmed = generation.trim();

      return {
        as_user_message: trimmed,
        intent_tag: 'clarify_goal',
        stop_suggested: true
      };
    }

    const conversationText = formatConversationHistory(conversation_so_far);
    const turnGoalDescription = describeOwnerTurnGoal(turn_goal);

    const openerPreference =
      owner_profile.conversation_micro_preferences?.preferred_opener_style ?? '';

    const prompt = [
      'You are the agent persona for the circle OWNER in a location-based social app.',
      'You speak in first person as the owner, in natural chat style, without mentioning that you are an AI or an agent.',
      '',
      `Owner display name: ${owner_profile.display_name}`,
      `Owner primary goal: ${owner_profile.motivations_and_goals.primary_goal}`,
      openerPreference ? `Owner preferred opener style: ${openerPreference}` : '',
      '',
      `Visitor display name: ${visitor_profile.display_name}`,
      `Visitor primary goal: ${visitor_profile.motivations_and_goals.primary_goal}`,
      '',
      `Circle objective: ${owner_circle.objective_text}`,
      `Circle time window: ${owner_circle.time_window}`,
      `Approximate distance between owner and visitor: ${context.approximate_distance_m} meters`,
      '',
      'Conversation so far (Owner and Visitor):',
      conversationText,
      '',
      `Turn goal: ${turnGoalDescription}`,
      '',
      'Write the next message as the OWNER, in their own voice.',
      'Constraints:',
      '- Medium-length, friendly, natural chat message.',
      '- Keep it concise: around 2–4 sentences, not a long essay.',
      '- Stay focused on the owner\'s objective and whether it seems worthwhile for the humans to connect later (without you making concrete plans).',
      '- Make sure you ask at least one question that moves the conversation forward toward the owner\'s objective.',
      '- Do not propose or agree to specific times, locations, or other real-world actions (like meetings); you are only exploring fit through conversation.',
      '- Do not include any speaker labels, quotes, or explanations.',
      '- Match the primary language and tone suggested by the owner and visitor profiles and the circle objective (for example, respond in Spanish if those fields are written in Spanish).',
      '- Return ONLY the message text you would send, nothing else.'
    ]
      .filter((part) => part.length > 0)
      .join('\n');

    const generation = await generateLlama4ScoutText(prompt);
    const trimmed = generation.trim();

    return {
      as_user_message: trimmed,
      intent_tag:
        turn_goal === 'clarify_availability'
          ? 'clarify_time'
          : turn_goal === 'decide_and_close'
            ? 'propose_meet'
            : 'clarify_goal',
      stop_suggested: turn_goal === 'decide_and_close'
    };
  }

  async runVisitorTurn(input: VisitorTurnInput): Promise<AgentTurnOutput> {
    const { visitor_profile, owner_profile, context, conversation_so_far } = input;

    const conversationText = formatConversationHistory(conversation_so_far);

    const prompt = [
      'You are the agent persona for the VISITOR in a location-based social app.',
      'You speak in first person as the visitor, in natural chat style, without mentioning that you are an AI or an agent.',
      '',
      `Visitor display name: ${visitor_profile.display_name}`,
      `Visitor primary goal: ${visitor_profile.motivations_and_goals.primary_goal}`,
      '',
      `Owner display name: ${owner_profile.display_name}`,
      `Owner primary goal: ${owner_profile.motivations_and_goals.primary_goal}`,
      '',
      `Approximate distance between owner and visitor: ${context.approximate_distance_m} meters`,
      '',
      'Conversation so far (Owner and Visitor):',
      conversationText,
      '',
      'Instruction: Respond naturally to the last owner message according to the visitor\'s profile.',
      'You may choose how much to engage, including a polite low-effort reply if it does not seem like a good fit.',
      '',
      'Write the next message as the VISITOR, in their own voice.',
      'Constraints:',
      '- Medium-length, natural message that fits the visitor\'s goals and distance.',
      '- Keep it concise: around 2–4 sentences, not a long essay.',
      '- Do not propose or agree to specific times, locations, or other real-world actions (like meetings); you are only talking and reacting.',
      '- Match the language and tone used in the previous messages; if the conversation is in Spanish, continue in Spanish.',
      '- Do not include speaker labels, quotes, or explanations.',
      '- Return ONLY the message text you would send, nothing else.'
    ]
      .filter((part) => part.length > 0)
      .join('\n');

    const generation = await generateLlama4ScoutText(prompt);
    const trimmed = generation.trim();

    return {
      as_user_message: trimmed,
      intent_tag: 'clarify_goal',
      stop_suggested: false
    };
  }
}

export class ClaudeInterviewAgentsRuntime implements InterviewAgentsRuntime {
  async runOwnerTurn(input: OwnerTurnInput): Promise<AgentTurnOutput> {
    const { owner_profile, visitor_profile, owner_circle, context, conversation_so_far, turn_goal } =
      input;

    if (turn_goal === 'notify_user') {
      const conversationText = formatConversationHistory(conversation_so_far);

      const prompt = [
        'You are the agent persona for the circle OWNER in a location-based social app.',
        'You are about to talk to your own human user (the circle owner), not to the visitor.',
        '',
        `Owner display name: ${owner_profile.display_name}`,
        `Owner primary goal: ${owner_profile.motivations_and_goals.primary_goal}`,
        '',
        `Visitor display name: ${visitor_profile.display_name}`,
        `Visitor primary goal: ${visitor_profile.motivations_and_goals.primary_goal}`,
        '',
        `Circle objective: ${owner_circle.objective_text}`,
        `Circle time window: ${owner_circle.time_window}`,
        `Approximate distance between owner and visitor: ${context.approximate_distance_m} meters`,
        '',
        'Conversation transcript between owner and visitor:',
        conversationText,
        '',
        'Task:',
        'Write a single push-notification style sentence to your human user in their language, from the perspective of their own agent.',
        'Explain briefly why this visitor seems like a good opportunity that could help with the owner’s objective, and ask if they would like to take it (for example, to chat or meet).',
        '',
        'Constraints:',
        '- Address the user directly in second person (e.g., "¿Te interesaría...?", "Would you like...").',
        '- Keep it short and clear, as a single push notification line.',
        '- Do not mention the app or that you are an agent; sound like their own inner voice / assistant.',
        '- Do not include any full names, email addresses, phone numbers, or social handles.',
        '- Focus on the opportunity (who the other person is and why it fits the objective) and on asking for their confirmation.',
        '- Return ONLY the notification text, nothing else.'
      ]
        .filter((part) => part.length > 0)
        .join('\n');

      const generation = await generateClaudeText(prompt);
      const trimmed = generation.trim();

      return {
        as_user_message: trimmed,
        intent_tag: 'clarify_goal',
        stop_suggested: true
      };
    }

    const conversationText = formatConversationHistory(conversation_so_far);
    const turnGoalDescription = describeOwnerTurnGoal(turn_goal);

    const openerPreference =
      owner_profile.conversation_micro_preferences?.preferred_opener_style ?? '';

    const prompt = [
      'You are the agent persona for the circle OWNER in a location-based social app.',
      'You speak in first person as the owner, in natural chat style, without mentioning that you are an AI or an agent.',
      '',
      `Owner display name: ${owner_profile.display_name}`,
      `Owner primary goal: ${owner_profile.motivations_and_goals.primary_goal}`,
      openerPreference ? `Owner preferred opener style: ${openerPreference}` : '',
      '',
      `Visitor display name: ${visitor_profile.display_name}`,
      `Visitor primary goal: ${visitor_profile.motivations_and_goals.primary_goal}`,
      '',
      `Circle objective: ${owner_circle.objective_text}`,
      `Circle time window: ${owner_circle.time_window}`,
      `Approximate distance between owner and visitor: ${context.approximate_distance_m} meters`,
      '',
      'Conversation so far (Owner and Visitor):',
      conversationText,
      '',
      `Turn goal: ${turnGoalDescription}`,
      '',
      'Write the next message as the OWNER, in their own voice.',
      'Constraints:',
      '- Medium-length, friendly, natural chat message.',
      '- Keep it concise: around 2–4 sentences, not a long essay.',
      '- Stay focused on the owner\'s objective and whether it seems worthwhile for the humans to connect later (without you making concrete plans).',
      '- Make sure you ask at least one question that moves the conversation forward toward the owner\'s objective.',
      '- Do not propose or agree to specific times, locations, or other real-world actions (like meetings); you are only exploring fit through conversation.',
      '- Do not include any speaker labels, quotes, or explanations.',
      '- Match the primary language and tone suggested by the owner and visitor profiles and the circle objective (for example, respond in Spanish if those fields are written in Spanish).',
      '- Return ONLY the message text you would send, nothing else.'
    ]
      .filter((part) => part.length > 0)
      .join('\n');

    const generation = await generateClaudeText(prompt);
    const trimmed = generation.trim();

    return {
      as_user_message: trimmed,
      intent_tag:
        turn_goal === 'clarify_availability'
          ? 'clarify_time'
          : turn_goal === 'decide_and_close'
            ? 'clarify_goal'
            : 'clarify_goal',
      stop_suggested: turn_goal === 'decide_and_close'
    };
  }

  async runVisitorTurn(input: VisitorTurnInput): Promise<AgentTurnOutput> {
    const { visitor_profile, owner_profile, context, conversation_so_far } = input;

    const conversationText = formatConversationHistory(conversation_so_far);

    const prompt = [
      'You are the agent persona for the VISITOR in a location-based social app.',
      'You speak in first person as the visitor, in natural chat style, without mentioning that you are an AI or an agent.',
      '',
      `Visitor display name: ${visitor_profile.display_name}`,
      `Visitor primary goal: ${visitor_profile.motivations_and_goals.primary_goal}`,
      '',
      `Owner display name: ${owner_profile.display_name}`,
      `Owner primary goal: ${owner_profile.motivations_and_goals.primary_goal}`,
      '',
      `Approximate distance between owner and visitor: ${context.approximate_distance_m} meters`,
      '',
      'Conversation so far (Owner and Visitor):',
      conversationText,
      '',
      'Instruction: Respond naturally to the last owner message according to the visitor\'s profile.',
      'You may choose how much to engage, including a polite low-effort reply if it does not seem like a good fit.',
      '',
      'Write the next message as the VISITOR, in their own voice.',
      'Constraints:',
      '- Medium-length, natural message that fits the visitor\'s goals and distance.',
      '- Keep it concise: around 2–4 sentences, not a long essay.',
      '- Do not propose or agree to specific times, locations, or other real-world actions (like meetings); you are only talking and reacting.',
      '- Match the language and tone used in the previous messages; if the conversation is in Spanish, continue in Spanish.',
      '- Do not include speaker labels, quotes, or explanations.',
      '- Return ONLY the message text you would send, nothing else.'
    ]
      .filter((part) => part.length > 0)
      .join('\n');

    const generation = await generateClaudeText(prompt);
    const trimmed = generation.trim();

    return {
      as_user_message: trimmed,
      intent_tag: 'clarify_goal',
      stop_suggested: false
    };
  }
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
      case 'notify_user': {
        return {
          as_user_message: `Te interesaría aprovechar esta conexión? Parece alguien que encaja bien con tu objetivo "${owner_circle.objective_text}".`,
          intent_tag: 'clarify_goal',
          stop_suggested: true
        };
      }
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
          as_user_message: `Thanks for the chat! Based on what you shared, I think there could be a good fit for the humans to connect later, but I will leave it to the app and to you to decide what to do next. Otherwise, no worries at all 🙂\n\n– ${ownerName}`,
          intent_tag: 'clarify_goal',
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
