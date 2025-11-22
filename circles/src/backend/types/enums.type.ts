import { z } from 'zod';

/**
 * Circle status enumeration
 */
export enum CircleStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  EXPIRED = 'expired',
}

export const circleStatusSchema = z.enum(['active', 'paused', 'expired']).transform((status) => {
  return status === 'active' ? CircleStatus.ACTIVE : status === 'paused' ? CircleStatus.PAUSED : CircleStatus.EXPIRED;
});

/**
 * Match type enumeration
 */
export enum MatchType {
  MATCH = 'match',
  SOFT_MATCH = 'soft_match',
}

export const matchTypeSchema = z.enum(['match', 'soft_match']);

/**
 * Match status enumeration
 */
export enum MatchStatus {
  PENDING_ACCEPT = 'pending_accept',
  ACTIVE = 'active',
  DECLINED = 'declined',
  EXPIRED = 'expired',
}

export const matchStatusSchema = z.enum(['pending_accept', 'active', 'declined', 'expired']);
