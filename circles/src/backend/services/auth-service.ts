import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import crypto from 'node:crypto';

import { emailService } from './email-service.js';
import { env } from '../config/env.js';
import { magicLinkTokenRepository } from '../repositories/magic-link-token-repository.js';
import { userRepository } from '../repositories/user-repository.js';
import { AppError } from '../types/app-error.type.js';
import { AuthPayload, PublicUser, User, CreateUserInput } from '../types/user.type.js';

export type SignupInput = {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type MagicLinkRequestInput = {
  email: string;
  firstName?: string;
};

type AuthResult = {
  token: string;
  user: PublicUser;
};

type MagicLinkResult = {
  success: boolean;
  message: string;
};

const MAGIC_LINK_EXPIRY_MINUTES = 15;

const toPublicUser = (user: User): PublicUser => {
  const { passwordHash: _passwordHash, ...rest } = user;
  return {
    ...rest,
    // Ensure dates are serializable
    createdAt: rest.createdAt instanceof Date ? rest.createdAt : new Date(rest.createdAt),
    updatedAt: rest.updatedAt instanceof Date ? rest.updatedAt : new Date(rest.updatedAt)
  };
};

const hashPassword = (plain: string): string => bcrypt.hashSync(plain, 10);

const verifyPassword = (plain: string, hash: string): boolean => {
  if (!hash) return false;
  return bcrypt.compareSync(plain, hash);
};

const signToken = (payload: AuthPayload): string =>
  jwt.sign(payload, env.jwtSecret, { expiresIn: '12h' });

const generateMagicToken = (): string => {
  return crypto.randomBytes(32).toString('hex');
};

class AuthService {
  /**
   * Traditional signup with password (for backwards compatibility)
   */
  async signup(input: SignupInput): Promise<AuthResult> {
    const existing = await userRepository.findByEmail(input.email);
    if (existing) {
      throw new AppError('Email already registered', 409);
    }

    const passwordHash = hashPassword(input.password);
    const createInput: CreateUserInput = { email: input.email, passwordHash };
    if (input.firstName !== undefined) {
      createInput.firstName = input.firstName;
    }
    if (input.lastName !== undefined) {
      createInput.lastName = input.lastName;
    }

    const user = await userRepository.create(createInput);
    const token = signToken({ userId: user.id, email: user.email });
    return { token, user: toPublicUser(user) };
  }

  /**
   * Traditional login with password (for backwards compatibility)
   */
  async login(input: LoginInput): Promise<AuthResult> {
    const user = await userRepository.findByEmail(input.email);
    if (!user) {
      throw new AppError('Invalid credentials', 401);
    }

    if (!user.passwordHash) {
      throw new AppError('This account uses magic link authentication', 401);
    }

    const valid = verifyPassword(input.password, user.passwordHash);
    if (!valid) {
      throw new AppError('Invalid credentials', 401);
    }

    const token = signToken({ userId: user.id, email: user.email });
    return { token, user: toPublicUser(user) };
  }

  /**
   * Request a magic link (for signup or login)
   */
  async requestMagicLink(input: MagicLinkRequestInput): Promise<MagicLinkResult> {
    const email = input.email.toLowerCase();
    const magicToken = generateMagicToken();
    const expiresAt = new Date(Date.now() + MAGIC_LINK_EXPIRY_MINUTES * 60 * 1000);

    // Create or update magic link token
    await magicLinkTokenRepository.create({
      email,
      token: magicToken,
      expiresAt
    });

    // Generate magic link URL
    const magicLink = `${env.apiUrl || 'http://localhost:3000'}/api/auth/verify-magic-link?token=${magicToken}`;

    // Send email with magic link
    try {
      await emailService.sendMagicLink(email, magicLink, input.firstName);
    } catch (error) {
      console.error('Failed to send magic link email:', error);
      throw new AppError('Failed to send magic link. Please try again.', 500);
    }

    return {
      success: true,
      message: `Magic link sent to ${email}`
    };
  }

  /**
   * Verify magic link and authenticate user
   */
  async verifyMagicLink(token: string): Promise<AuthResult> {
    // Find token
    const magicLinkToken = await magicLinkTokenRepository.findByToken(token);
    if (!magicLinkToken) {
      throw new AppError('Invalid or expired magic link', 401);
    }

    // Check expiration
    if (new Date() > magicLinkToken.expiresAt) {
      await magicLinkTokenRepository.deleteByEmail(magicLinkToken.email);
      throw new AppError('Magic link has expired', 401);
    }

    const email = magicLinkToken.email;

    // Find or create user
    let user = await userRepository.findByEmail(email);
    if (!user) {
      // Create new user with magic link (no password)
      const createInput: CreateUserInput = {
        email,
        profile: { interests: [] }
      };
      user = await userRepository.create(createInput);

      // Send welcome email (fire and forget)
      emailService.sendWelcome(email, user.firstName ?? undefined).catch((err) => {
        console.error('Failed to send welcome email:', err);
      });
    }

    // Delete used token
    await magicLinkTokenRepository.deleteByEmail(email);

    // Generate JWT token
    const jwtToken = signToken({ userId: user.id, email: user.email });
    return { token: jwtToken, user: toPublicUser(user) };
  }
}

export const authService = new AuthService();
