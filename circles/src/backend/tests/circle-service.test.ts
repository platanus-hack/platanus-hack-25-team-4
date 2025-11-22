import { describe, expect, it, beforeEach } from 'vitest';

import { resetRepositories } from './helpers/resetRepositories.js';
import { authService } from '../services/authService.js';
import { circleService } from '../services/circleService.js';
import { AppError } from '../types/app-error.js';

const buildCircleInput = (userId: string) => ({
  userId,
  objectiveText: 'Play tennis',
  centerLat: -34.6037,
  centerLon: -58.3816,
  radiusMeters: 500,
  startAt: new Date(),
  expiresAt: new Date(Date.now() + 60 * 60 * 1000)
});

describe('circleService', () => {
  beforeEach(() => {
    resetRepositories();
  });

  it('creates, lists, updates, and deletes circles', () => {
    const user = authService.signup({ email: 'circle@example.com', password: 'strongpassword' });

    const created = circleService.create(buildCircleInput(user.user.id));
    expect(created.objectiveText).toBe('Play tennis');

    const listed = circleService.listByUser(user.user.id);
    expect(listed).toHaveLength(1);

    const updated = circleService.update(created.id, user.user.id, {
      objectiveText: 'Play padel',
      radiusMeters: 700
    });
    expect(updated.objectiveText).toBe('Play padel');
    expect(updated.radiusMeters).toBe(700);

    circleService.remove(created.id, user.user.id);
    const afterDelete = circleService.listByUser(user.user.id);
    expect(afterDelete).toHaveLength(0);
  });

  it('prevents updates by non-owners', () => {
    const owner = authService.signup({ email: 'owner@example.com', password: 'password123' });
    const other = authService.signup({ email: 'other@example.com', password: 'password456' });

    const circle = circleService.create(buildCircleInput(owner.user.id));

    expect(() =>
      circleService.update(circle.id, other.user.id, { objectiveText: 'Attempted takeover' })
    ).toThrow(AppError);

    expect(() => circleService.remove(circle.id, other.user.id)).toThrow(AppError);
  });
});
