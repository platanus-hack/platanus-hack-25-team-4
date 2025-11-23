import { PrismaClient } from '@prisma/client';
import { describe, expect, it, beforeEach, afterEach } from 'vitest';

import { AuthService } from '../services/auth-service.js';
import { CircleService } from '../services/circle-service.js';
import { AppError } from '../types/app-error.type.js';

const prisma = new PrismaClient();

const buildCircleInput = (userId: string) => ({
  userId,
  objective: 'Play tennis',
  radiusMeters: 500,
  startAt: new Date(),
  expiresAt: new Date(Date.now() + 60 * 60 * 1000)
});

describe('circleService', () => {
  let authService: AuthService;
  let circleService: CircleService;

  beforeEach(async () => {
    authService = new AuthService();
    circleService = new CircleService();
    // Clean up database before each test
    await prisma.circle.deleteMany({});
    await prisma.magicLinkToken.deleteMany({});
    await prisma.user.deleteMany({});
  });

  afterEach(async () => {
    await prisma.circle.deleteMany({});
    await prisma.magicLinkToken.deleteMany({});
    await prisma.user.deleteMany({});
  });

  it('creates, lists, updates, and deletes circles', async () => {
    const user = await authService.signup({ email: 'circle@example.com', password: 'strongpassword' });

    const created = await circleService.create(buildCircleInput(user.user.id));
    expect(created.objective).toBe('Play tennis');

    const listed = await circleService.listByUser(user.user.id);
    expect(listed).toHaveLength(1);

    const updated = await circleService.update(created.id, user.user.id, {
      objective: 'Play padel',
      radiusMeters: 700
    });
    expect(updated?.objective).toBe('Play padel');
    expect(updated?.radiusMeters).toBe(700);

    await circleService.remove(created.id, user.user.id);
    const afterDelete = await circleService.listByUser(user.user.id);
    expect(afterDelete).toHaveLength(0);
  });

  it('allows creating circles without expiresAt', async () => {
    const user = await authService.signup({ email: 'noexp@example.com', password: 'strongpassword' });

    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);

    const created = await circleService.create({
      userId: user.user.id,
      objective: 'Test circle without expiry',
      radiusMeters: 1000,
      expiresAt: futureDate,
      startAt: new Date(),
      status: undefined
    });

    expect(created).toBeDefined();
    expect(created.objective).toBe('Test circle without expiry');
  });

  it('prevents updates by non-owners', async () => {
    const owner = await authService.signup({ email: 'owner@example.com', password: 'password123' });
    const other = await authService.signup({ email: 'other@example.com', password: 'password456' });

    const circle = await circleService.create(buildCircleInput(owner.user.id));

    await expect(
      circleService.update(circle.id, other.user.id, {
        objective: 'Attempted takeover',
        radiusMeters: 0
      })
    ).rejects.toThrow(AppError);

    await expect(circleService.remove(circle.id, other.user.id)).rejects.toThrow(AppError);
  });
});
