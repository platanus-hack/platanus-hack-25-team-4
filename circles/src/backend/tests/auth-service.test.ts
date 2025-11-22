import { describe, expect, it, beforeEach } from 'vitest';

import { authService } from '../services/auth-service.js';
import { AppError } from '../types/app-error.type.js';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

describe('authService', () => {
  beforeEach(async () => {
    // Clean up database before each test
    await prisma.magicLinkToken.deleteMany({});
    await prisma.user.deleteMany({});
  });

  it('signs up and logs in a user', async () => {
    const email = 'user@example.com';
    const password = 'strongpassword';

    const signupResult = await authService.signup({ email, password });
    expect(signupResult.user.email).toBe(email);
    expect(typeof signupResult.token).toBe('string');
    expect(signupResult.token).not.toHaveLength(0);

    const loginResult = await authService.login({ email, password });
    expect(loginResult.user.id).toBe(signupResult.user.id);
    expect(loginResult.token).not.toHaveLength(0);
  });

  it('rejects duplicate email signup', async () => {
    const email = 'duplicate@example.com';
    const password = 'anotherstrongpassword';

    await authService.signup({ email, password });

    await expect(authService.signup({ email, password })).rejects.toThrow(AppError);
  });

  it('rejects invalid login', async () => {
    await expect(
      authService.login({ email: 'missing@example.com', password: 'test' })
    ).rejects.toThrow(AppError);
  });
});
