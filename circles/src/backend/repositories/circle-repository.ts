import { PrismaClient as client } from '@prisma/client';

import { Circle, CreateCircleInput } from '../types/circle.type.js';
import { CircleStatus } from '../types/enums.type.js';

export type UpdateCircleInput = Partial<Omit<CreateCircleInput, 'userId'>> & {
  status?: CircleStatus;
};

export class CircleRepository {
  /**
   * Create a new circle
   */
  async create(input: CreateCircleInput): Promise<Circle> {
    const circle = await client.circle.create({
      data: {
        userId: input.userId,
        objective: input.objective,
        centerLat: input.centerLat,
        centerLon: input.centerLon,
        radiusMeters: input.radiusMeters,
        startAt: input.startAt,
        expiresAt: input.expiresAt,
        status: input.status ?? CircleStatus.ACTIVE
      }
    });

    return this.mapToCircle(circle);
  }

  /**
   * Find circle by ID
   */
  async findById(id: string): Promise<Circle | undefined> {
    const circle = await client.circle.findUnique({
      where: { id }
    });

    return circle ? this.mapToCircle(circle) : undefined;
  }

  /**
   * Find all circles for a user
   */
  async findByUser(userId: string): Promise<Circle[]> {
    const circles = await client.circle.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' }
    });

    return circles.map((c: {
      id: string;
      userId: string;
      objective: string;
      centerLat: number | null;
      centerLon: number | null;
      radiusMeters: number | null;
      startAt: Date | null;
      expiresAt: Date | null;
      status: CircleStatus;
      createdAt: Date;
      updatedAt: Date;
    }) => this.mapToCircle(c));
  }

  /**
   * Update circle
   */
  async update(id: string, input: UpdateCircleInput): Promise<Circle | undefined> {
    const circle = await client.circle.update({
      where: { id },
      data: {
        objective: input.objective ?? undefined,
        centerLat: input.centerLat ?? undefined,
        centerLon: input.centerLon ?? undefined,
        radiusMeters: input.radiusMeters ?? undefined,
        startAt: input.startAt ?? undefined,
        expiresAt: input.expiresAt ?? undefined,
        status: input.status ?? undefined
      }
    });

    return this.mapToCircle(circle);
  }

  /**
   * Delete circle
   */
  async delete(id: string): Promise<void> {
    await client.circle.delete({
      where: { id }
    });
  }

  /**
   * Map Prisma circle to our Circle type
   */
  private mapToCircle(circle: {
    id: string;
    userId: string;
    objective: string;
    centerLat: number | null;
    centerLon: number | null;
    radiusMeters: number | null;
    startAt: Date | null;
    expiresAt: Date | null;
    status: CircleStatus;
    createdAt: Date;
    updatedAt: Date;
  }): Circle {
    return {
      id: circle.id,
      userId: circle.userId,
      objective: circle.objective,
      centerLat: circle.centerLat,
      centerLon: circle.centerLon,
      radiusMeters: circle.radiusMeters,
      startAt: circle.startAt,
      expiresAt: circle.expiresAt,
      status: circle.status,
      createdAt: circle.createdAt,
      updatedAt: circle.updatedAt
    };
  }
}

export const circleRepository = new CircleRepository();
