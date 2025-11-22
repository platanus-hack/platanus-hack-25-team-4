import { Router } from 'express';
import { z } from 'zod';

import { validateBody } from '../middlewares/validate-body.middleware.js';
import { authService, SignupInput } from '../services/auth-service.js';
import { asyncHandler } from '../utils/async-handler.util.js';

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

export const authRouter = Router();

authRouter.post(
  '/auth/signup',
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

    const result = authService.signup(signupInput);
    res.status(201).json(result);
  })
);

authRouter.post(
  '/auth/login',
  validateBody(loginSchema),
  asyncHandler(async (req, res) => {
    const { email, password } = loginSchema.parse(req.body);
    const result = authService.login({ email, password });
    res.json(result);
  })
);
