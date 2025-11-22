import { describe, expect, it, beforeEach } from 'vitest';

import { resetRepositories } from './helpers/resetRepositories.js';
import { authService } from '../services/authService.js';
import { AppError } from '../types/app-error.js';

describe('authService', () => {
  beforeEach(() => {
    resetRepositories();
  });

  it('signs up and logs in a user', () => {
    const email = 'user@example.com';
    const password = 'strongpassword';

    const signupResult = authService.signup({ email, password });
    expect(signupResult.user.email).toBe(email);
    expect(typeof signupResult.token).toBe('string');
    expect(signupResult.token).not.toHaveLength(0);

    const loginResult = authService.login({ email, password });
    expect(loginResult.user.id).toBe(signupResult.user.id);
    expect(loginResult.token).not.toHaveLength(0);
  });

  it('rejects duplicate email signup', () => {
    const email = 'duplicate@example.com';
    const password = 'anotherstrongpassword';

    authService.signup({ email, password });

    expect(() => authService.signup({ email, password })).toThrow(AppError);
  });

  it('rejects invalid login', () => {
    expect(() => authService.login({ email: 'missing@example.com', password: 'test' })).toThrow(
      AppError
    );
  });
});
