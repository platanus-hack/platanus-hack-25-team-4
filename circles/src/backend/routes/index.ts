import { Router } from 'express';

import { authRouter } from './auth.js';
import { circlesRouter } from './circles.js';
import { healthRouter } from './health.js';
import { usersRouter } from './users.js';

export const apiRouter = Router();

apiRouter.use(healthRouter);
apiRouter.use(authRouter);
apiRouter.use(circlesRouter);
apiRouter.use(usersRouter);
