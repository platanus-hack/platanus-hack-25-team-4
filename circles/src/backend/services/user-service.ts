import { UserRepository } from '../repositories/user-repository.js';
import { AppError } from '../types/app-error.type.js';
import { User, PublicUser, UpdateUserInput } from '../types/user.type.js';

/**
 * Convert User to PublicUser (removes sensitive data)
 */
const toPublicUser = (user: User): PublicUser => {
  const { passwordHash: _passwordHash, ...rest } = user;
  return rest;
};

export class UserService {
  private readonly userRepository: UserRepository;

  constructor() {
    this.userRepository = new UserRepository();
  }
  /**
   * Get user by ID
   */
  async getById(id: string): Promise<PublicUser | undefined> {
    const user = await this.userRepository.findById(id);
    return user ? toPublicUser(user) : undefined;
  }

  /**
   * Get user by email
   */
  async getByEmail(email: string): Promise<PublicUser | undefined> {
    const user = await this.userRepository.findByEmail(email);
    return user ? toPublicUser(user) : undefined;
  }

  /**
   * Update user (with ownership check)
   */
  async update(id: string, userId: string, input: UpdateUserInput): Promise<PublicUser> {
    // Verify ownership
    if (id !== userId) {
      throw new AppError('Unauthorized', 403);
    }

    const user = await this.userRepository.findById(id);
    if (!user) {
      throw new AppError('User not found', 404);
    }

    const updated = await this.userRepository.update(id, input);
    if (!updated) {
      throw new AppError('Failed to update user', 500);
    }

    return toPublicUser(updated);
  }

  /**
   * Update user position (latitude and longitude)
   */
  async updatePosition(userId: string, centerLat: number, centerLon: number): Promise<PublicUser> {
    const user = await this.userRepository.findById(userId);
    if (!user) {
      throw new AppError('User not found', 404);
    }

    const updated = await this.userRepository.updatePosition(userId, centerLat, centerLon);
    if (!updated) {
      throw new AppError('Failed to update position', 500);
    }

    return toPublicUser(updated);
  }

  /**
   * Delete user (with ownership check)
   */
  async delete(id: string, userId: string): Promise<void> {
    // Verify ownership
    if (id !== userId) {
      throw new AppError('Unauthorized', 403);
    }

    const user = await this.userRepository.findById(id);
    if (!user) {
      throw new AppError('User not found', 404);
    }

    await this.userRepository.delete(id);
  }
}