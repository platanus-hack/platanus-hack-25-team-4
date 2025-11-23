import { createApp } from './app.js';
import { env } from './config/env.js';
import { initializeObserver } from './infrastructure/observer/index.js';
import { logger } from './utils/logger.util.js';

// Initialize observer system
initializeObserver();
logger.info('Observer system initialized');

const app = createApp();

app.listen(env.port, () => {
  logger.info(`Server listening on port ${env.port} (${env.nodeEnv})`);
});
