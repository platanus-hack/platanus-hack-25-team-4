import { randomUUID } from 'node:crypto';

import { Circle, CreateCircleInput } from '../types/circle.type.js';
import { CircleStatus } from '../types/enums.type.js';

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
      objective: input.objective,
      centerLat: input.centerLat,
      centerLon: input.centerLon,
      radiusMeters: input.radiusMeters,
      startAt: input.startAt,
      expiresAt: input.expiresAt,
      status: CircleStatus.ACTIVE,
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
