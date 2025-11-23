import { generateClaudeText } from './anthropicClient.js';
import { generateLlama4ScoutText } from './bedrockLlamaClient.js';
import type { JudgeDecision, JudgeInput } from './types.js';
import { logger } from '../../utils/logger.util.js';

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
        should_notify: false,
        summary_text: 'Summary of agent interaction: they talked, but there was no clear signal to justify notifying the humans.'
      };
    }

    return {
      should_notify: true,
      summary_text:
        'Summary of agent interaction: they talked about concrete plans or interest in meeting, which seems worth notifying the humans about.'
    };
  }
}

type LlmJudgeResponse = {
  should_notify: boolean;
  summary_text?: string;
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
      '{ "should_notify": true or false, "summary_text": string }',
      '',
      'Rules:',
      '- Consider whether the conversation suggests a promising real-world interaction that could help the owner move toward their objective, even if the agents did not schedule a specific time or place.',
      '- Be conservative: only set "should_notify" to true if the conversation suggests a promising real-world interaction.',
      '- The "summary_text" MUST be a very short, single-sentence summary of the conversation, in the main language of the transcript (often Spanish).',
      '- The "summary_text" MUST begin EXACTLY with: "Summary of agent interaction:".',
      '- After that fixed prefix, continue with a brief description of what they talked about (for example: "they talked about posibles proyectos de IA y coordinar un café").',
      '- Keep "summary_text" under 240 characters, with no line breaks.',
      '- When "should_notify" is false, still include "summary_text" but you can briefly say that the interaction did not seem worth notifying about.',
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
      logger.error(`Failed to parse Judge JSON from LLM: ${message}`, error);
      return {
        should_notify: false
      };
    }

    if (!parsed || typeof parsed.should_notify !== 'boolean') {
      return {
        should_notify: false
      };
    }

    const decision: JudgeDecision = {
      should_notify: parsed.should_notify === true
    };

    if (typeof parsed.summary_text === 'string' && parsed.summary_text.trim().length > 0) {
      decision.summary_text = parsed.summary_text.trim();
    }

    return decision;
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
      '{ "should_notify": true or false, "summary_text": string }',
      '',
      'Rules:',
      '- Consider whether the conversation suggests a promising real-world interaction that could help the owner move toward their objective, even if the agents did not schedule a specific time or place.',
      '- Be conservative: only set "should_notify" to true if the conversation suggests a promising real-world interaction.',
      '- The "summary_text" MUST be a very short, single-sentence summary of the conversation, in the main language of the transcript (often Spanish).',
      '- The "summary_text" MUST begin EXACTLY with: "Summary of agent interaction:".',
      '- After that fixed prefix, continue with a brief description of what they talked about (for example: "they talked about posibles proyectos de IA y coordinar un café").',
      '- Keep "summary_text" under 240 characters, with no line breaks.',
      '- When "should_notify" is false, still include "summary_text" but you can briefly say that the interaction did not seem worth notifying about.',
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
      logger.error(`Failed to parse Judge JSON from Claude: ${message}`, error);
      return {
        should_notify: false
      };
    }

    if (!parsed || typeof parsed.should_notify !== 'boolean') {
      return {
        should_notify: false
      };
    }

    const decision: JudgeDecision = {
      should_notify: parsed.should_notify === true
    };

    if (typeof parsed.summary_text === 'string' && parsed.summary_text.trim().length > 0) {
      decision.summary_text = parsed.summary_text.trim();
    }

    return decision;
  }
}
