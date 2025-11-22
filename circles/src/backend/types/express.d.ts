import { AuthPayload } from './user.type.ts';

declare module 'express-serve-static-core' {
  interface Request {
    user?: AuthPayload;
  }
}
