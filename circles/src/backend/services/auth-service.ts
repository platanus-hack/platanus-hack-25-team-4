import * as bcrypt from 'bcryptjs';
// eslint-disable-next-line import/default
import jwt from 'jsonwebtoken';

import { env } from '../config/env.js';
import type { CreateUserInput } from '../repositories/user-repository.js';
import { userRepository } from '../repositories/user-repository.js';
import { AppError } from '../types/app-error.type.js';
import { AuthPayload, PublicUser, User } from '../types/user.type.js';

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

type AuthResult = {
  token: string;
  user: PublicUser;
};

const toPublicUser = (user: User): PublicUser => {
  const { passwordHash: _passwordHash, ...rest } = user;
  return rest;
};

const hashPassword = (plain: string): string => bcrypt.hashSync(plain, 10);

const verifyPassword = (plain: string, hash: string): boolean => bcrypt.compareSync(plain, hash);

const signToken = (payload: AuthPayload): string =>
  jwt.sign(payload, env.jwtSecret, { expiresIn: '12h' });

class AuthService {
  signup(input: SignupInput): AuthResult {
    const existing = userRepository.findByEmail(input.email);
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

    const user = userRepository.create(createInput);
    const token = signToken({ userId: user.id, email: user.email });
    return { token, user: toPublicUser(user) };
  }

  login(input: LoginInput): AuthResult {
    const user = userRepository.findByEmail(input.email);
    if (!user) {
      throw new AppError('Invalid credentials', 401);
    }

    const valid = verifyPassword(input.password, user.passwordHash);
    if (!valid) {
      throw new AppError('Invalid credentials', 401);
    }

    const token = signToken({ userId: user.id, email: user.email });
    return { token, user: toPublicUser(user) };
  }
}

export const authService = new AuthService();
