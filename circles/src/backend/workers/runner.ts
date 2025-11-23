import { CleanupWorker } from './cleanup-worker.js';
import { StabilityWorker } from './stability-worker.js';
import { logger } from '../utils/logger.util.js';
/**
 * Worker Runner
 * Orchestrates startup and lifecycle of all background workers
 */
export class WorkerRunner {
  private stabilityWorker: StabilityWorker;
  private cleanupWorker: CleanupWorker;

  constructor() {
    this.stabilityWorker = new StabilityWorker();
    this.cleanupWorker = new CleanupWorker();
  }

  /**
   * Start all workers
   * Note: Mission processing is handled by BullMQ worker (missionWorkerRunner.ts)
   */
  startAll(): void {
    logger.info('Starting all workers...');

    // Start stability worker (5 second interval)
    this.stabilityWorker.start(5000);

    // Start cleanup worker (10 minute interval)
    this.cleanupWorker.start(10 * 60 * 1000);

    logger.info('All workers started');
  }

  /**
   * Start only stability worker
   */
  startStabilityWorker(): void {
    logger.info('Starting stability worker...');
    this.stabilityWorker.start(5000);
  }

  /**
   * Start only cleanup worker
   */
  startCleanupWorker(): void {
    logger.info('Starting cleanup worker...');
    this.cleanupWorker.start(10 * 60 * 1000);
  }

  /**
   * Stop all workers
   */
  stopAll(): void {
    logger.info('Stopping all workers...');
    this.stabilityWorker.stop();
    this.cleanupWorker.stop();
    logger.info('All workers stopped');
  }
}

/**
 * Determine which worker(s) to start based on environment variable
 * Note: 'mission' is no longer supported - use missionWorkerRunner.ts instead
 */
function getWorkersToStart(): string[] {
  const workerEnv = process.env.WORKERS || 'all';

  switch (workerEnv.toLowerCase()) {
    case 'stability':
      return ['stability'];
    case 'cleanup':
      return ['cleanup'];
    case 'all':
    default:
      return ['stability', 'cleanup'];
  }
}

/**
 * Main entry point for worker runner
 * Can be invoked with: npm run workers
 */
export async function startWorkers(): Promise<void> {
  logger.info('Collision matching system workers starting...');

  const runner = new WorkerRunner();
  const workersToStart = getWorkersToStart();

  if (workersToStart.includes('stability')) {
    runner.startStabilityWorker();
  }
  if (workersToStart.includes('cleanup')) {
    runner.startCleanupWorker();
  }

  // Handle graceful shutdown
  process.on('SIGTERM', () => {
    logger.info('SIGTERM received, stopping workers...');
    runner.stopAll();
    process.exit(0);
  });

  process.on('SIGINT', () => {
    logger.info('SIGINT received, stopping workers...');
    runner.stopAll();
    process.exit(0);
  });

  logger.info('Workers running. Started:', workersToStart);
  logger.info('Set WORKERS environment variable to: stability, cleanup, or all (default)');
  logger.info('Note: Mission processing uses BullMQ (start with: npm run dev:mission-worker)');
}

// Start workers if this is the main module
if (process.argv[1]?.endsWith('runner.ts') || process.argv[1]?.endsWith('runner.js')) {
  startWorkers().catch(error => {
    logger.error('Failed to start workers', error);
    process.exit(1);
  });
}
