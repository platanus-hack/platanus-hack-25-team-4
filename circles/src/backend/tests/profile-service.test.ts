import { PrismaClient } from '@prisma/client';
import { describe, expect, it, beforeEach } from 'vitest';

import { AuthService } from '../services/auth-service.js';
import { ProfileService } from '../services/profile-service.js';

const prisma = new PrismaClient();
const authService = new AuthService();
const profileService = new ProfileService();

describe('profileService', () => {
  beforeEach(async () => {
    // Clean up database before each test
    await prisma.magicLinkToken.deleteMany({});
    await prisma.user.deleteMany({});
  });

  it('returns and updates a user profile', async () => {
    const email = 'profile@example.com';
    const password = 'strongpassword';
    const signup = await authService.signup({ email, password });

    const initialProfile = await profileService.getProfile(signup.user.id);
    expect(initialProfile).not.toBeNull();
    expect(initialProfile!.interests).toEqual([]);
    expect(initialProfile!.bio).toBeUndefined();
    expect(initialProfile!.profileCompleted).toBeFalsy();

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

    const saved = await profileService.updateProfile(signup.user.id, updatedProfile);
    expect(saved).toEqual(updatedProfile);

    const fetched = await profileService.getProfile(signup.user.id);
    expect(fetched).not.toBeNull();
    expect(fetched).toEqual(updatedProfile);
  });
});
