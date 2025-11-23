import { UserRepository } from '../repositories/user-repository.js';
import { AppError } from '../types/app-error.type.js';
import { PublicUser, UserProfile } from '../types/user.type.js';

const ensureUser = async (userRepository: UserRepository, userId: string): Promise<PublicUser> => {
  const user = await userRepository.findById(userId);
  if (!user) {
    throw new AppError('User not found', 404);
  }

  const { passwordHash: _passwordHash, ...rest } = user;
  return rest;
};

export class ProfileService {
  private readonly userRepository: UserRepository;

  constructor() {
    this.userRepository = new UserRepository();
  }
  /**
   * Get user profile
   */
  async getProfile(userId: string): Promise<UserProfile | null> {
    return (await ensureUser(this.userRepository, userId)).profile;
  }

  /**
   * Update user profile
   */
  async updateProfile(userId: string, profile: UserProfile): Promise<UserProfile | null> {
    const updated = await this.userRepository.updateProfile(userId, profile);
    if (!updated) {
      throw new AppError('User not found', 404);
    }
    return updated.profile;
  }
}
