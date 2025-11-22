import { AuthPayload } from './user.js';

declare module 'express-serve-static-core' {
  interface Request {
    user?: AuthPayload;
  }
}
