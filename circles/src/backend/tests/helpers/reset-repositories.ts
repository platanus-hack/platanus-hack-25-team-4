import { circleRepository } from '../../repositories/circle-repository.js';
import { userRepository } from '../../repositories/user-repository.js';

export const resetRepositories = (): void => {
  circleRepository.clear();
  userRepository.clear();
};
