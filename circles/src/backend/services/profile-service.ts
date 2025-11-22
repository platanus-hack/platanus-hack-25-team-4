import { userRepository } from '../repositories/user-repository.js';
import { AppError } from '../types/app-error.type.js';
import { PublicUser, UserProfile } from '../types/user.type.js';

const ensureUser = async (userId: string): Promise<PublicUser> => {
  const user = await userRepository.findById(userId);
  if (!user) {
    throw new AppError('User not found', 404);
  }

  const { passwordHash: _passwordHash, ...rest } = user;
  return rest;
};

class ProfileService {
  /**
   * Get user profile
   */
  async getProfile(userId: string): Promise<UserProfile | null> {
    return (await ensureUser(userId)).profile;
  }

  /**
   * Update user profile
   */
  async updateProfile(userId: string, profile: UserProfile): Promise<UserProfile | null> {
    const updated = await userRepository.updateProfile(userId, profile);
    if (!updated) {
      throw new AppError('User not found', 404);
    }
    return updated.profile;
  }
}

export const profileService = new ProfileService();
