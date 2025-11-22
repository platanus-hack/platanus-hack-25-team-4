import { userRepository } from '../repositories/user-repository.js';
import { AppError } from '../types/app-error.type.js';
import { PublicUser, UserProfile } from '../types/user.type.js';

const ensureUser = (userId: string): PublicUser => {
  const user = userRepository.findById(userId);
  if (!user) {
    throw new AppError('User not found', 404);
  }

  const { passwordHash: _passwordHash, ...rest } = user;
  return rest;
};

class ProfileService {
  getProfile(userId: string): UserProfile {
    return ensureUser(userId).profile;
  }

  updateProfile(userId: string, profile: UserProfile): UserProfile {
    const updated = userRepository.updateProfile(userId, profile);
    if (!updated) {
      throw new AppError('User not found', 404);
    }
    return updated.profile;
  }
}

export const profileService = new ProfileService();
