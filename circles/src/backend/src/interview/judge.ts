import { generateClaudeText } from './anthropicClient.js';
import { generateLlama4ScoutText } from './bedrockLlamaClient.js';
import type { JudgeDecision, JudgeInput } from './types.js';
import { logger } from '../utils/logger.js';

export interface InterviewJudge {
  evaluate(input: JudgeInput): Promise<JudgeDecision>;
}

export class MockInterviewJudge implements InterviewJudge {
  async evaluate(input: JudgeInput): Promise<JudgeDecision> {
    const { transcript } = input;

    const fullConversation = transcript.map((turn) => turn.message).join('\n');

    const containsConcreteSignal =
      fullConversation.toLowerCase().includes('meet') ||
      fullConversation.toLowerCase().includes('coffee') ||
      fullConversation.toLowerCase().includes('café') ||
      fullConversation.toLowerCase().includes('cafe') ||
      fullConversation.toLowerCase().includes('reunirnos') ||
      fullConversation.toLowerCase().includes('vernos') ||
      fullConversation.toLowerCase().includes('let\'s') ||
      fullConversation.toLowerCase().includes('lets');

    if (!containsConcreteSignal) {
      return {
        should_notify: false
      };
    }

    return {
      should_notify: true
    };
  }
}

type LlmJudgeResponse = {
  should_notify: boolean;
};

const extractJsonFromText = (raw: string): string => {
  const firstBrace = raw.indexOf('{');
  const lastBrace = raw.lastIndexOf('}');

  if (firstBrace === -1 || lastBrace === -1 || lastBrace < firstBrace) {
    return raw;
  }

  return raw.slice(firstBrace, lastBrace + 1);
};

export class BedrockInterviewJudge implements InterviewJudge {
  async evaluate(input: JudgeInput): Promise<JudgeDecision> {
    const transcriptLines =
      input.transcript.length === 0
        ? ['(no messages)']
        : input.transcript.map((turn) => {
            const speakerLabel = turn.speaker === 'owner' ? 'Owner' : 'Visitor';
            return `${speakerLabel}: ${turn.message}`;
          });

    const prompt = [
      'You are the Judge agent in a location-based social app.',
      'Your job is to decide whether an agent-to-agent interview made enough progress toward the OWNER\'s objective to bother the humans with a notification.',
      '',
      `Owner objective: ${input.owner_objective}`,
      '',
      'Conversation transcript (in order):',
      ...transcriptLines,
      '',
      'Decide whether to notify the humans now.',
      '',
      'Output format:',
      'Return a SINGLE JSON object with exactly these fields:',
      '{ "should_notify": true or false }',
      '',
      'Rules:',
      '- Consider whether the conversation suggests a promising real-world interaction that could help the owner move toward their objective, even if the agents did not schedule a specific time or place.',
      '- Be conservative: only set "should_notify" to true if the conversation suggests a promising real-world interaction.',
      '- Do not add any extra keys, comments, or explanations.',
      '- Do not wrap the JSON in markdown fences or any other formatting.',
      '- Return ONLY the JSON, nothing else.'
    ].join('\n');

    const raw = await generateLlama4ScoutText(prompt);
    const jsonText = extractJsonFromText(raw);
    let parsed: LlmJudgeResponse | undefined;

    try {
      parsed = JSON.parse(jsonText);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      logger.error(`Failed to parse Judge JSON from LLM: ${message}`);
      return {
        should_notify: false
      };
    }

    if (!parsed || typeof parsed.should_notify !== 'boolean') {
      return {
        should_notify: false
      };
    }

    return {
      should_notify: parsed.should_notify === true
    };
  }
}

export class ClaudeInterviewJudge implements InterviewJudge {
  async evaluate(input: JudgeInput): Promise<JudgeDecision> {
    const transcriptLines =
      input.transcript.length === 0
        ? ['(no messages)']
        : input.transcript.map((turn) => {
            const speakerLabel = turn.speaker === 'owner' ? 'Owner' : 'Visitor';
            return `${speakerLabel}: ${turn.message}`;
          });

    const prompt = [
      'You are the Judge agent in a location-based social app.',
      'Your job is to decide whether an agent-to-agent interview made enough progress toward the OWNER\'s objective to bother the humans with a notification.',
      '',
      `Owner objective: ${input.owner_objective}`,
      '',
      'Conversation transcript (in order):',
      ...transcriptLines,
      '',
      'Decide whether to notify the humans now.',
      '',
      'Output format:',
      'Return a SINGLE JSON object with exactly these fields:',
      '{ "should_notify": true or false }',
      '',
      'Rules:',
      '- Consider whether the conversation suggests a promising real-world interaction that could help the owner move toward their objective, even if the agents did not schedule a specific time or place.',
      '- Be conservative: only set "should_notify" to true if the conversation suggests a promising real-world interaction.',
      '- Do not add any extra keys, comments, or explanations.',
      '- Do not wrap the JSON in markdown fences or any other formatting.',
      '- Return ONLY the JSON, nothing else.'
    ].join('\n');

    const raw = await generateClaudeText(prompt);
    const jsonText = extractJsonFromText(raw);
    let parsed: LlmJudgeResponse | undefined;

    try {
      parsed = JSON.parse(jsonText);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      logger.error(`Failed to parse Judge JSON from Claude: ${message}`);
      return {
        should_notify: false
      };
    }

    if (!parsed || typeof parsed.should_notify !== 'boolean') {
      return {
        should_notify: false
      };
    }

    return {
      should_notify: parsed.should_notify === true
    };
  }
}
