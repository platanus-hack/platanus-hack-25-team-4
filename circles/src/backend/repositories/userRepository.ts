import { randomUUID } from 'node:crypto';

import { User, UserProfile } from '../types/user.js';

export type CreateUserInput = {
  email: string;
  passwordHash: string;
  firstName?: string;
  lastName?: string;
};

const usersById = new Map<string, User>();
const usersByEmail = new Map<string, User>();

export class UserRepository {
  create(input: CreateUserInput): User {
    const id = randomUUID();
    const newUser: User = {
      id,
      email: input.email.toLowerCase(),
      ...(input.firstName ? { firstName: input.firstName } : {}),
      ...(input.lastName ? { lastName: input.lastName } : {}),
      passwordHash: input.passwordHash,
      profile: { interests: [] }
    };

    usersById.set(id, newUser);
    usersByEmail.set(newUser.email, newUser);
    return newUser;
  }

  findByEmail(email: string): User | undefined {
    return usersByEmail.get(email.toLowerCase());
  }

  findById(id: string): User | undefined {
    return usersById.get(id);
  }

  updateProfile(id: string, profile: UserProfile): User | undefined {
    const existing = usersById.get(id);
    if (!existing) {
      return undefined;
    }

    const updated: User = { ...existing, profile };
    usersById.set(id, updated);
    usersByEmail.set(updated.email, updated);
    return updated;
  }

  clear(): void {
    usersById.clear();
    usersByEmail.clear();
  }
}

export const userRepository = new UserRepository();
