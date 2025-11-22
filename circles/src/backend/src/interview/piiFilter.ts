import type { UserProfile } from './types.js';
import { logger } from '../../utils/logger.util.js';

const REDACTED_NAME_TOKEN = '[REDACTED-NAME]';
const REDACTED_CONTACT_TOKEN = '[REDACTED-CONTACT]';
const REDACTED_HANDLE_TOKEN = '[REDACTED-HANDLE]';

const EMAIL_REGEX = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
const PHONE_REGEX = /\+?[0-9][0-9\s\-().]{7,}[0-9]/g;
const HANDLE_REGEX = /@[A-Za-z0-9_]{3,}/g;

const escapeForRegExp = (value: string): string =>
  value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const extractDisplayNameCandidates = (displayName: string): string[] => {
  const mainPart = displayName.split(',')[0]?.trim() ?? '';
  if (!mainPart) {
    return [];
  }

  const words = mainPart.split(/\s+/);

  for (const rawWord of words) {
    const word = rawWord.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/g, '');
    if (word.length < 2) {
      continue;
    }

    if (!/^[A-ZÁÉÍÓÚÜÑ]/.test(word)) {
      continue;
    }

    return [word];
  }

  return [];
};

const extractOpenerNameCandidates = (opener: string | undefined): string[] => {
  if (!opener) {
    return [];
  }

  const candidates = new Set<string>();

  const patterns: RegExp[] = [
    /\bsoy\s+([^\s,!.?]+)/gi,
    /\bmi nombre es\s+([^\s,!.?]+)/gi,
    /\bmy name is\s+([^\s,!.?]+)/gi,
    /\bI['’]m\s+([^\s,!.?]+)/gi
  ];

  for (const pattern of patterns) {
    const matches = opener.matchAll(pattern);
    for (const match of matches) {
      const group = match[1];
      if (!group) {
        continue;
      }

      const cleaned = group.replace(/^[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$/g, '');
      if (cleaned.length >= 2) {
        candidates.add(cleaned);
      }
    }
  }

  return Array.from(candidates);
};

const collectProfileNameTokens = (profile: UserProfile): string[] => {
  const tokens = new Set<string>();

  for (const name of extractDisplayNameCandidates(profile.display_name)) {
    tokens.add(name);
  }

  for (const openerName of extractOpenerNameCandidates(
    profile.conversation_micro_preferences?.preferred_opener_style
  )) {
    tokens.add(openerName);
  }

  return Array.from(tokens);
};

export const redactAgentMessage = (message: string, profile: UserProfile): string => {
  let result = message;

  const nameTokens = collectProfileNameTokens(profile);

  for (const token of nameTokens) {
    const pattern = new RegExp(`\\b${escapeForRegExp(token)}\\b`, 'gi');
    result = result.replace(pattern, REDACTED_NAME_TOKEN);
  }

  result = result.replace(EMAIL_REGEX, REDACTED_CONTACT_TOKEN);
  result = result.replace(PHONE_REGEX, REDACTED_CONTACT_TOKEN);
  result = result.replace(HANDLE_REGEX, REDACTED_HANDLE_TOKEN);

  if (result !== message) {
    logger.info(
      [
        'PII filter – message redacted:',
        `\tbefore: ${message}`,
        `\tafter:  ${result}`
      ].join('\n')
    );
  }

  return result;
};
