import { Anthropic } from '@anthropic-ai/sdk';

import { logger } from '../../utils/logger.util.js';

const defaultModelId = process.env.ANTHROPIC_MODEL_ID ?? 'claude-haiku-4-5';

const apiKey = process.env.ANTHROPIC_API_KEY;

if (!apiKey) {
  logger.warn('ANTHROPIC_API_KEY is not set; Claude-based runtimes will fail at runtime.');
}

const anthropicClient =
  apiKey !== undefined
    ? new Anthropic({
        apiKey
      })
    : undefined;

const delay = (ms: number): Promise<void> =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

type ErrorWithStatus = {
  status?: number;
};

type ErrorWithNestedError = {
  error?: unknown;
};

type ErrorWithType = {
  type?: string;
};

const hasStatus = (error: unknown): error is ErrorWithStatus =>
  typeof error === 'object' && error !== null && 'status' in error;

const hasErrorProp = (error: unknown): error is ErrorWithNestedError =>
  typeof error === 'object' && error !== null && 'error' in error;

const hasTypeProp = (error: unknown): error is ErrorWithType =>
  typeof error === 'object' && error !== null && 'type' in error;

const isRateLimitError = (error: unknown): boolean => {
  if (!error || typeof error !== 'object') {
    return false;
  }

  if (hasStatus(error) && error.status === 429) {
    return true;
  }

  if (!hasErrorProp(error)) {
    return false;
  }

  const maybeErrorWrapper = error.error;
  if (!hasErrorProp(maybeErrorWrapper)) {
    return false;
  }

  const inner = maybeErrorWrapper.error;
  if (hasTypeProp(inner) && inner.type === 'rate_limit_error') {
    return true;
  }

  return false;
};

export const generateClaudeText = async (prompt: string): Promise<string> => {
  if (!anthropicClient) {
    throw new Error('Anthropic client is not configured (missing ANTHROPIC_API_KEY).');
  }

  const maxRetries = 3;
  let lastError: unknown;

  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    try {
      const response = await anthropicClient.messages.create({
        model: defaultModelId,
        max_tokens: 512,
        temperature: 0.7,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      });

      const textChunks: string[] = [];

      for (const block of response.content) {
        if (block.type === 'text') {
          textChunks.push(block.text);
        }
      }

      if (textChunks.length === 0) {
        logger.warn('Claude returned no text content; returning empty string.');
        return '';
      }

      return textChunks.join('\n').trim();
    } catch (error) {
      lastError = error;

      if (!isRateLimitError(error) || attempt === maxRetries) {
        throw error;
      }

      const backoffMs = 1000 * 2 ** attempt;
      logger.warn(
        `Claude rate limit hit (attempt ${attempt + 1} of ${maxRetries + 1}); retrying after ${backoffMs}ms.`
      );
      await delay(backoffMs);
    }
  }

  throw lastError instanceof Error
    ? lastError
    : new Error('Unknown error while calling Claude with retries.');
};
