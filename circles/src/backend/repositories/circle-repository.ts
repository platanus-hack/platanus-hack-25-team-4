import { randomUUID } from 'node:crypto';

import { Circle, CircleStatus } from '../types/circle.type.js';

export type CreateCircleInput = {
  userId: string;
  objectiveText: string;
  centerLat: number;
  centerLon: number;
  radiusMeters: number;
  startAt: Date;
  expiresAt: Date;
};

export type UpdateCircleInput = Partial<Omit<CreateCircleInput, 'userId'>> & {
  status?: CircleStatus;
};

const circlesById = new Map<string, Circle>();

export class CircleRepository {
  create(input: CreateCircleInput): Circle {
    const now = new Date();
    const circle: Circle = {
      id: randomUUID(),
      userId: input.userId,
      objectiveText: input.objectiveText,
      centerLat: input.centerLat,
      centerLon: input.centerLon,
      radiusMeters: input.radiusMeters,
      startAt: input.startAt,
      expiresAt: input.expiresAt,
      status: 'active',
      createdAt: now,
      updatedAt: now
    };

    circlesById.set(circle.id, circle);
    return circle;
  }

  findById(id: string): Circle | undefined {
    return circlesById.get(id);
  }

  findByUser(userId: string): Circle[] {
    return Array.from(circlesById.values()).filter((circle) => circle.userId === userId);
  }

  update(id: string, input: UpdateCircleInput): Circle | undefined {
    const existing = circlesById.get(id);
    if (!existing) {
      return undefined;
    }

    const updated: Circle = {
      ...existing,
      ...input,
      updatedAt: new Date()
    };

    circlesById.set(id, updated);
    return updated;
  }

  delete(id: string): void {
    circlesById.delete(id);
  }

  clear(): void {
    circlesById.clear();
  }
}

export const circleRepository = new CircleRepository();
