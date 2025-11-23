import { Router } from 'express';

import { authRouter } from './auth.js';
import { chatsRouter } from './chats.js';
import { circlesRouter } from './circles.js';
import { collisionsRouter } from './collisions.js';
import { healthRouter } from './health.js';
import { locationsRouter } from './locations.js';
import { matchesRouter } from './matches.js';
import { missionsRouter } from './missions.js';
import { observerRouter } from './observer.js';
import { usersRouter } from './users.js';

export const apiRouter = Router();

apiRouter.use(healthRouter);
apiRouter.use(authRouter);
apiRouter.use(circlesRouter);
apiRouter.use(collisionsRouter);
apiRouter.use(missionsRouter);
apiRouter.use(usersRouter);
apiRouter.use(chatsRouter);
apiRouter.use(locationsRouter);
apiRouter.use(matchesRouter);
apiRouter.use('/observer', observerRouter);
