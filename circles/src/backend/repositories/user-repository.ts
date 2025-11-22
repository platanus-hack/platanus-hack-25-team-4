import { randomUUID } from 'node:crypto';

import { User, UserProfile, CreateUserInput } from '../types/user.type.js';

const usersById = new Map<string, User>();
const usersByEmail = new Map<string, User>();

export class UserRepository {
  create(input: CreateUserInput): User {
    const id = randomUUID();
    const now = new Date();
    const newUser: User = {
      id,
      email: input.email.toLowerCase(),
      firstName: input.firstName ?? null,
      lastName: input.lastName ?? null,
      passwordHash: input.passwordHash,
      profile: input.profile ?? { interests: [] },
      createdAt: now,
      updatedAt: now
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

    const updated: User = { ...existing, profile, updatedAt: new Date() };
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
