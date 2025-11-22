import { circleRepository } from '../../repositories/circleRepository.js';
import { userRepository } from '../../repositories/userRepository.js';

export const resetRepositories = (): void => {
  circleRepository.clear();
  userRepository.clear();
};
