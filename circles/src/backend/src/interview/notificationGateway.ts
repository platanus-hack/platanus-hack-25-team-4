import type { NotificationPayload } from './types.js';
import { logger } from '../../utils/logger.util.js';

export interface NotificationGateway {
  notifySuccessfulInteraction(payload: NotificationPayload): Promise<void>;
}

export class LoggingNotificationGateway implements NotificationGateway {
  async notifySuccessfulInteraction(payload: NotificationPayload): Promise<void> {
    const { mission_id, owner_user_id, visitor_user_id, notification_text } = payload;

    logger.info(
      `Mock notification sent for mission ${mission_id} (owner=${owner_user_id}, visitor=${visitor_user_id}): ${notification_text}`
    );
  }
}

