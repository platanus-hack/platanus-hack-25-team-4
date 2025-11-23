import { prisma } from '../lib/prisma.js';
import type { Circle, CreateCircleInput, UpdateCircleInput } from '../types/circle.type.js';
import { CircleStatus } from '../types/enums.type.js'

export class CircleRepository {
  /**
   * Create a new circle
   */
  async create(input: CreateCircleInput): Promise<Circle> {
    const circle = await prisma.circle.create({
      data: {
        userId: input.userId,
        objective: input.objective,
        radiusMeters: input.radiusMeters,
        startAt: input.startAt,
        expiresAt: input.expiresAt ?? null,
        status: input.status ?? CircleStatus.ACTIVE
      }
    });

    return this.mapToCircle(circle);
  }

  /**
   * Find circle by ID
   */
  async findById(id: string): Promise<Circle | undefined> {
    const circle = await prisma.circle.findUnique({
      where: { id }
    });

    return circle ? this.mapToCircle(circle) : undefined;
  }

  /**
   * Find all circles for a user
   */
  async findByUser(userId: string): Promise<Circle[]> {
    const circles = await prisma.circle.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' }
    });

    return circles.map((c: {
      id: string;
      userId: string;
      objective: string;
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
    const data: UpdateCircleInput = {
      objective: input.objective,
      radiusMeters: input.radiusMeters
    };

    if (input.expiresAt !== undefined) {
      data.expiresAt = input.expiresAt;
    }

    const circle = await prisma.circle.update({
      where: { id },
      data
    });

    return this.mapToCircle(circle);
  }

  /**
   * Delete circle
   */
  async delete(id: string): Promise<void> {
    await prisma.circle.delete({
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
