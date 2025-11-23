/**
 * Obfuscate sensitive data for logging purposes
 */

export const obfuscatePassword = (password: string): string => {
  if (!password || password.length === 0) return '***';
  if (password.length <= 2) return '*'.repeat(password.length);
  // Show first 2 chars, then stars, then last 1 char
  return password.slice(0, 2) + '*'.repeat(Math.max(3, password.length - 3)) + password.slice(-1);
};

export const obfuscateEmail = (email: string): string => {
  if (!email || !email.includes('@')) return '***';
  const parts = email.split('@');
  if (parts.length !== 2) return '***';
  const [local, domain] = parts;
  if (!local || !domain || local.length <= 2) {
    return (local ?? '') + '***@' + (domain ?? '');
  }
  // Show first 2 chars of local part
  return local.slice(0, 2) + '*'.repeat(local.length - 2) + '@' + domain;
};

export const obfuscateSensitive = (obj: Record<string, unknown>): Record<string, unknown> => {
  const result = { ...obj };
  
  const sensitiveFields = ['password', 'passwordHash', 'token', 'apiKey', 'secret'];
  
  for (const field of sensitiveFields) {
    if (field in result && typeof result[field] === 'string') {
      const value = result[field];
      if (typeof value === 'string') {
        result[field] = '*'.repeat(Math.min(10, value.length));
      }
    }
  }
  
  return result;
};
