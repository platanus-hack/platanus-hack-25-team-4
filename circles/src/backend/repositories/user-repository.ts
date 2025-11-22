import { prisma } from '../lib/prisma.js';
import { User, UserProfile, CreateUserInput } from '../types/user.type.js';

export class UserRepository {
  /**
   * Create a new user
   */
  async create(input: CreateUserInput): Promise<User> {
    const user = await prisma.user.create({
      data: {
        email: input.email.toLowerCase(),
        firstName: input.firstName ?? null,
        lastName: input.lastName ?? null,
        passwordHash: input.passwordHash ?? null,
        profile: input.profile ?? { interests: [] }
      }
    });

    return this.mapToUser(user);
  }

  /**
   * Find user by email
   */
  async findByEmail(email: string): Promise<User | undefined> {
    const user = await prisma.user.findUnique({
      where: { email: email.toLowerCase() }
    });

    return user ? this.mapToUser(user) : undefined;
  }

  /**
   * Find user by ID
   */
  async findById(id: string): Promise<User | undefined> {
    const user = await prisma.user.findUnique({
      where: { id }
    });

    return user ? this.mapToUser(user) : undefined;
  }

  /**
   * Update user profile
   */
  async updateProfile(id: string, profile: UserProfile): Promise<User | undefined> {
    const user = await prisma.user.update({
      where: { id },
      data: { profile }
    });

    return this.mapToUser(user);
  }

  /**
   * Update user
   */
  async update(id: string, data: Partial<CreateUserInput>): Promise<User | undefined> {
    const user = await prisma.user.update({
      where: { id },
      data: {
        firstName: data.firstName ?? undefined,
        lastName: data.lastName ?? undefined,
        passwordHash: data.passwordHash ?? undefined,
        profile: data.profile ?? undefined
      }
    });

    return this.mapToUser(user);
  }

  /**
   * Delete user
   */
  async delete(id: string): Promise<void> {
    await prisma.user.delete({
      where: { id }
    });
  }

  /**
   * Map Prisma user to our User type
   */
  private mapToUser(user: {
    id: string;
    email: string;
    firstName: string | null;
    lastName: string | null;
    passwordHash: string | null;
    profile: unknown;
    createdAt: Date;
    updatedAt: Date;
  }): User {
    return {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      passwordHash: user.passwordHash,
      // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
      profile: user.profile as UserProfile | null,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt
    };
  }
}

export const userRepository = new UserRepository();
