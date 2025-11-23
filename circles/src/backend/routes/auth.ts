import { Router } from 'express';
import { z } from 'zod';

import { authRateLimiter } from '../middlewares/rate-limiter.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import { AuthService, SignupInput, MagicLinkRequestInput } from '../services/auth-service.js';
import { AppError } from '../types/app-error.type.js';
import { asyncHandler } from '../utils/async-handler.util.js';

// Traditional password-based schemas
const signupSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  firstName: z.string().trim().min(1).optional(),
  lastName: z.string().trim().min(1).optional()
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

// Magic link schemas
const magicLinkRequestSchema = z.object({
  email: z.string().email(),
  firstName: z.string().trim().min(1).optional()
});

export const authRouter = Router();

// Service instances
const authService = new AuthService();

/**
 * Traditional signup endpoint
 * POST /api/auth/signup
 * Response: { token: string, user: PublicUser }
 */
authRouter.post(
  '/auth/signup',
  authRateLimiter,
  validateBody(signupSchema),
  asyncHandler(async (req, res) => {
    const { email, password, firstName, lastName } = signupSchema.parse(req.body);
    const signupInput: SignupInput = { email, password };

    if (firstName !== undefined) {
      signupInput.firstName = firstName;
    }
    if (lastName !== undefined) {
      signupInput.lastName = lastName;
    }

    const result = await authService.signup(signupInput);
    res.status(201).json({ token: result.token, user: result.user });
  })
);

/**
 * Traditional login endpoint
 * POST /api/auth/login
 */
authRouter.post(
  '/auth/login',
  authRateLimiter,
  validateBody(loginSchema),
  asyncHandler(async (req, res) => {
    const { email, password } = loginSchema.parse(req.body);
    const result = await authService.login({ email, password });
    res.json({ token: result.token, user: result.user });
  })
);

/**
 * Request magic link for signup/login
 * POST /api/auth/magic-link/request
 * Body: { email: string, firstName?: string }
 * Response: { success: boolean, message: string }
 */
authRouter.post(
  '/auth/magic-link/request',
  authRateLimiter,
  validateBody(magicLinkRequestSchema),
  asyncHandler(async (req, res) => {
    const { email, firstName } = magicLinkRequestSchema.parse(req.body);
    const input: MagicLinkRequestInput = { email };

    if (firstName !== undefined) {
      input.firstName = firstName;
    }

    const result = await authService.requestMagicLink(input);
    res.json(result);
  })
);

/**
 * Verify magic link and get JWT token
 * GET /api/auth/verify-magic-link?token=<token>
 * Response: { token: string, user: PublicUser }
 */
authRouter.get(
  '/auth/verify-magic-link',
  authRateLimiter,
  asyncHandler(async (req, res) => {
    const { token } = req.query;

    if (!token || typeof token !== 'string') {
      throw new AppError('Magic link token is required', 400);
    }

    const result = await authService.verifyMagicLink(token);
    res.json({ token: result.token, user: result.user });
  })
);
