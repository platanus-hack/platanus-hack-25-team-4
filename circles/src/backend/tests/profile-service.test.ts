import { describe, expect, it, beforeEach } from 'vitest';

import { authService } from '../services/auth-service.js';
import { profileService } from '../services/profile-service.js';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

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
    expect(initialProfile?.interests).toEqual([]);

    const updatedProfile = {
      interests: ['ai', 'tennis'],
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
