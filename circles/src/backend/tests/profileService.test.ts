import { describe, expect, it, beforeEach } from 'vitest';

import { resetRepositories } from './helpers/resetRepositories.js';
import { authService } from '../services/authService.js';
import { profileService } from '../services/profileService.js';

describe('profileService', () => {
  beforeEach(() => {
    resetRepositories();
  });

  it('returns and updates a user profile', () => {
    const email = 'profile@example.com';
    const password = 'strongpassword';
    const signup = authService.signup({ email, password });

    const initialProfile = profileService.getProfile(signup.user.id);
    expect(initialProfile.interests).toEqual([]);

    const updatedProfile = {
      interests: ['ai', 'tennis'],
      socialStyle: 'friendly',
      boundaries: ['no late nights'],
      availability: 'mornings'
    };

    const saved = profileService.updateProfile(signup.user.id, updatedProfile);
    expect(saved).toEqual(updatedProfile);

    const fetched = profileService.getProfile(signup.user.id);
    expect(fetched).toEqual(updatedProfile);
  });
});
