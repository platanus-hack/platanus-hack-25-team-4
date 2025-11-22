/**
 * Magic link token model matching Prisma schema
 */
export type MagicLinkToken = {
  id: string;
  email: string;
  token: string;
  expiresAt: Date;
  createdAt: Date;
};

/**
 * Magic link creation input
 */
export type CreateMagicLinkTokenInput = {
  email: string;
  token: string;
  expiresAt: Date;
};

/**
 * Magic link verification result
 */
export type MagicLinkVerificationResult = {
  valid: boolean;
  expired: boolean;
  email?: string;
  error?: string;
};

