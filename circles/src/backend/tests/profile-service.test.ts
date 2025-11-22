import { describe, expect, it, beforeEach } from 'vitest';

import { resetRepositories } from './helpers/reset-repositories.js';
import { authService } from '../services/auth-service.js';
import { profileService } from '../services/profile-service.js';

describe('profileService', () => {
  beforeEach(() => {
    resetRepositories();
  });

  it('returns and updates a user profile', () => {
    const email = 'profile@example.com';
    const password = 'strongpassword';
    const signup = authService.signup({ email, password });

    const initialProfile = profileService.getProfile(signup.user.id);
    expect(initialProfile).not.toBeNull();
    expect(initialProfile!.interests).toEqual([]);
    expect(initialProfile!.bio).toBe('');
    expect(initialProfile!.profileCompleted).toBe(false);

    const updatedProfile = {
      bio: 'I love AI and playing tennis',
      interests: [
        { title: 'AI', description: 'Interested in machine learning' },
        { title: 'Tennis', description: 'Play tennis on weekends' }
      ],
      profileCompleted: true,
      socialStyle: 'friendly',
      boundaries: ['no late nights'],
      availability: 'mornings'
    };

    const saved = profileService.updateProfile(signup.user.id, updatedProfile);
    expect(saved).toEqual(updatedProfile);

    const fetched = profileService.getProfile(signup.user.id);
    expect(fetched).not.toBeNull();
    expect(fetched).toEqual(updatedProfile);
  });
});
