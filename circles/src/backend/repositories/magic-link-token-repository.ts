import { PrismaClient as client } from '@prisma/client';

import { CreateMagicLinkTokenInput, MagicLinkToken } from '../types/magic-link-token.type.js';

export class MagicLinkTokenRepository {
  /**
   * Create a new magic link token
   */
  async create(input: CreateMagicLinkTokenInput): Promise<MagicLinkToken> {
    // Delete old token if exists
    await client.magicLinkToken.deleteMany({
      where: { email: input.email.toLowerCase() }
    });

    const token = await client.magicLinkToken.create({
      data: {
        email: input.email.toLowerCase(),
        token: input.token,
        expiresAt: input.expiresAt
      }
    });

    return this.mapToMagicLinkToken(token);
  }

  /**
   * Find token by token string
   */
  async findByToken(token: string): Promise<MagicLinkToken | undefined> {
    const result = await client.magicLinkToken.findUnique({
      where: { token }
    });

    return result ? this.mapToMagicLinkToken(result) : undefined;
  }

  /**
   * Find token by email
   */
  async findByEmail(email: string): Promise<MagicLinkToken | undefined> {
    const result = await client.magicLinkToken.findUnique({
      where: { email: email.toLowerCase() }
    });

    return result ? this.mapToMagicLinkToken(result) : undefined;
  }

  /**
   * Delete token by ID
   */
  async delete(id: string): Promise<void> {
    await client.magicLinkToken.delete({
      where: { id }
    });
  }

  /**
   * Delete token by email
   */
  async deleteByEmail(email: string): Promise<void> {
    await client.magicLinkToken.deleteMany({
      where: { email: email.toLowerCase() }
    });
  }

  /**
   * Delete token by token string
   */
  async deleteByToken(token: string): Promise<void> {
    await client.magicLinkToken.deleteMany({
      where: { token }
    });
  }

  /**
   * Clean up expired tokens
   */
  async deleteExpired(): Promise<void> {
    await client.magicLinkToken.deleteMany({
      where: {
        expiresAt: {
          lt: new Date()
        }
      }
    });
  }

  /**
   * Map Prisma token to our MagicLinkToken type
   */
  private mapToMagicLinkToken(token: {
    id: string;
    email: string;
    token: string;
    expiresAt: Date;
    createdAt: Date;
  }): MagicLinkToken {
    return {
      id: token.id,
      email: token.email,
      token: token.token,
      expiresAt: token.expiresAt,
      createdAt: token.createdAt
    };
  }
}

export const magicLinkTokenRepository = new MagicLinkTokenRepository();
