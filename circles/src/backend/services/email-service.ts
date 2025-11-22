import { AwsSesEmailService } from './aws-ses-email-service.js';
import { env } from '../config/env.js';
import { logger } from '../utils/logger.util.js';

export type EmailOptions = {
  to: string;
  subject: string;
  html: string;
  text?: string;
};

// Use AWS SES in production if credentials are provided, otherwise use dev mode
let emailService: {
  sendMagicLink(email: string, magicLink: string, firstName?: string): Promise<void>;
  sendWelcome(email: string, firstName?: string): Promise<void>;
};

if (env.nodeEnv === 'production' && env.awsAccessKeyId && env.awsSecretAccessKey) {
  // Production: AWS SES
  emailService = new AwsSesEmailService();
} else {
  // Development: Console logging
  class DevEmailService {
    async sendMagicLink(email: string, magicLink: string, firstName?: string): Promise<void> {
      const name = firstName || 'User';
      logger.info(`📧 Magic link sent to ${email}`);
      console.log('\n🔗 MAGIC LINK (DEV MODE):');
      console.log(`To: ${email}`);
      console.log(`Name: ${name}`);
      console.log(`Link: ${magicLink}`);
      console.log('\n');
    }

    async sendWelcome(email: string, firstName?: string): Promise<void> {
      const name = firstName || 'User';
      logger.info(`📧 Welcome email sent to ${email}`);
      console.log(`✅ Welcome to Circles, ${name}!\n`);
    }
  }

  emailService = new DevEmailService();
}

export { emailService };
