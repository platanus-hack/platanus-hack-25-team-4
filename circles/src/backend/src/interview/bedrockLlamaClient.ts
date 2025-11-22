import { BedrockRuntimeClient, InvokeModelCommand } from '@aws-sdk/client-bedrock-runtime';

import { logger } from '../../utils/logger.util.js';

const defaultRegion = process.env.AWS_REGION ?? process.env.AWS_DEFAULT_REGION ?? 'us-east-1';
const defaultModelId =
  process.env.BEDROCK_INFERENCE_PROFILE_ID ?? 'us.meta.llama4-scout-17b-instruct-v1:0';

const client = new BedrockRuntimeClient({
  region: defaultRegion
});

export const generateLlama4ScoutText = async (prompt: string): Promise<string> => {
  const command = new InvokeModelCommand({
    modelId: defaultModelId,
    contentType: 'application/json',
    accept: 'application/json',
    body: JSON.stringify({
      prompt,
      max_gen_len: 512,
      temperature: 0.7,
      top_p: 0.9
    })
  });

  const response = await client.send(command);
  const bodyBytes = response.body;

  if (!bodyBytes) {
    logger.warn('Empty response body from Bedrock');
    return '';
  }

  const decoded = new TextDecoder('utf-8').decode(bodyBytes);

  try {
    const parsed = JSON.parse(decoded);
    if (typeof parsed?.generation === 'string') {
      return parsed.generation;
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    logger.warn(`Failed to parse Bedrock response JSON, returning raw text: ${message}`);
  }

  return decoded;
};
