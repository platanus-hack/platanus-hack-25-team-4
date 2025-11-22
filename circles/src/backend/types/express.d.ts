import type { AuthPayload } from './user.type.js';

declare module 'express-serve-static-core' {
  interface Request {
    user?: AuthPayload;
  }
}
