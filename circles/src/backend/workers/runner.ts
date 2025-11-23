import { CleanupWorker } from './cleanup-worker.js';
import { MissionWorker } from './mission-worker.js';
import { StabilityWorker } from './stability-worker.js';

/**
 * Worker Runner
 * Orchestrates startup and lifecycle of all background workers
 */
export class WorkerRunner {
  private stabilityWorker: StabilityWorker;
  private missionWorker: MissionWorker;
  private cleanupWorker: CleanupWorker;

  constructor() {
    this.stabilityWorker = new StabilityWorker();
    this.missionWorker = new MissionWorker(3); // Process up to 3 missions in parallel
    this.cleanupWorker = new CleanupWorker();
  }

  /**
   * Start all workers
   */
  startAll(): void {
    console.info('Starting all workers...');

    // Start stability worker (5 second interval)
    this.stabilityWorker.start(5000);

    // Start mission worker (10 second interval)
    this.missionWorker.start(10000);

    // Start cleanup worker (10 minute interval)
    this.cleanupWorker.start(10 * 60 * 1000);

    console.info('All workers started');
  }

  /**
   * Start only stability worker
   */
  startStabilityWorker(): void {
    console.info('Starting stability worker...');
    this.stabilityWorker.start(5000);
  }

  /**
   * Start only mission worker
   */
  startMissionWorker(): void {
    console.info('Starting mission worker...');
    this.missionWorker.start(10000);
  }

  /**
   * Start only cleanup worker
   */
  startCleanupWorker(): void {
    console.info('Starting cleanup worker...');
    this.cleanupWorker.start(10 * 60 * 1000);
  }

  /**
   * Stop all workers
   */
  stopAll(): void {
    console.info('Stopping all workers...');
    this.stabilityWorker.stop();
    this.missionWorker.stop();
    this.cleanupWorker.stop();
    console.info('All workers stopped');
  }
}

/**
 * Determine which worker(s) to start based on environment variable
 */
function getWorkersToStart(): string[] {
  const workerEnv = process.env.WORKERS || 'all';

  switch (workerEnv.toLowerCase()) {
    case 'stability':
      return ['stability'];
    case 'mission':
      return ['mission'];
    case 'cleanup':
      return ['cleanup'];
    case 'all':
    default:
      return ['stability', 'mission', 'cleanup'];
  }
}

/**
 * Main entry point for worker runner
 * Can be invoked with: npm run workers
 */
export async function startWorkers(): Promise<void> {
  console.info('Collision matching system workers starting...');

  const runner = new WorkerRunner();
  const workersToStart = getWorkersToStart();

  if (workersToStart.includes('stability')) {
    runner.startStabilityWorker();
  }
  if (workersToStart.includes('mission')) {
    runner.startMissionWorker();
  }
  if (workersToStart.includes('cleanup')) {
    runner.startCleanupWorker();
  }

  // Handle graceful shutdown
  process.on('SIGTERM', () => {
    console.info('SIGTERM received, stopping workers...');
    runner.stopAll();
    process.exit(0);
  });

  process.on('SIGINT', () => {
    console.info('SIGINT received, stopping workers...');
    runner.stopAll();
    process.exit(0);
  });

  console.info('Workers running. Started:', workersToStart);
  console.info('Set WORKERS environment variable to: stability, mission, cleanup, or all (default)');
}

// Start workers if this is the main module
if (process.argv[1]?.endsWith('runner.ts') || process.argv[1]?.endsWith('runner.js')) {
  startWorkers().catch(error => {
    console.error('Failed to start workers', error);
    process.exit(1);
  });
}
