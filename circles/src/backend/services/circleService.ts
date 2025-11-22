import {
  circleRepository,
  CreateCircleInput,
  UpdateCircleInput
} from '../repositories/circleRepository.js';
import { AppError } from '../types/app-error.js';
import { Circle } from '../types/circle.js';

const ensureOwnership = (circle: Circle, userId: string): void => {
  if (circle.userId !== userId) {
    throw new AppError('Circle not found', 404);
  }
};

class CircleService {
  create(input: CreateCircleInput): Circle {
    return circleRepository.create(input);
  }

  listByUser(userId: string): Circle[] {
    return circleRepository.findByUser(userId);
  }

  getById(id: string, userId: string): Circle {
    const circle = circleRepository.findById(id);
    if (!circle) {
      throw new AppError('Circle not found', 404);
    }
    ensureOwnership(circle, userId);
    return circle;
  }

  update(id: string, userId: string, input: UpdateCircleInput): Circle {
    const circle = circleRepository.findById(id);
    if (!circle) {
      throw new AppError('Circle not found', 404);
    }
    ensureOwnership(circle, userId);

    const updated = circleRepository.update(id, input);
    if (!updated) {
      throw new AppError('Circle not found', 404);
    }
    return updated;
  }

  remove(id: string, userId: string): void {
    const circle = circleRepository.findById(id);
    if (!circle) {
      throw new AppError('Circle not found', 404);
    }
    ensureOwnership(circle, userId);
    circleRepository.delete(id);
  }
}

export const circleService = new CircleService();
