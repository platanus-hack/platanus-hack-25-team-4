import { circleRepository, UpdateCircleInput } from '../repositories/circle-repository.js';
import { AppError } from '../types/app-error.type.js';
import { Circle, CreateCircleInput } from '../types/circle.type.js';

const ensureOwnership = (circle: Circle, userId: string): void => {
  if (circle.userId !== userId) {
    throw new AppError('Circle not found', 404);
  }
};

class CircleService {
  /**
   * Create a new circle
   */
  async create(input: CreateCircleInput): Promise<Circle> {
    return circleRepository.create(input);
  }

  /**
   * List all circles for a user
   */
  async listByUser(userId: string): Promise<Circle[]> {
    return circleRepository.findByUser(userId);
  }

  /**
   * Get circle by ID (with ownership check)
   */
  async getById(id: string, userId: string): Promise<Circle> {
    const circle = await circleRepository.findById(id);
    if (!circle) {
      throw new AppError('Circle not found', 404);
    }
    ensureOwnership(circle, userId);
    return circle;
  }

  /**
   * Update circle (with ownership check)
   */
  async update(id: string, userId: string, input: UpdateCircleInput): Promise<Circle> {
    const circle = await circleRepository.findById(id);
    if (!circle) {
      throw new AppError('Circle not found', 404);
    }
    ensureOwnership(circle, userId);

    const updated = await circleRepository.update(id, input);
    if (!updated) {
      throw new AppError('Circle not found', 404);
    }
    return updated;
  }

  /**
   * Delete circle (with ownership check)
   */
  async remove(id: string, userId: string): Promise<void> {
    const circle = await circleRepository.findById(id);
    if (!circle) {
      throw new AppError('Circle not found', 404);
    }
    ensureOwnership(circle, userId);
    await circleRepository.delete(id);
  }
}

export const circleService = new CircleService();
