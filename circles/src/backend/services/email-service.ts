import { AwsSesEmailService } from './aws-ses-email-service.js';
import { ResendEmailService } from './resend-email-service.js';
import { env } from '../config/env.js';
import { logger } from '../utils/logger.util.js';

export type EmailOptions = {
  to: string;
  subject: string;
  html: string;
  text?: string;
};

// Email service interface
interface EmailServiceInterface {
  sendMagicLink(email: string, magicLink: string, firstName?: string): Promise<void>;
  sendWelcome(email: string, firstName?: string): Promise<void>;
}

// Development email service for logging
class DevEmailService implements EmailServiceInterface {
  async sendMagicLink(email: string, magicLink: string, firstName?: string): Promise<void> {
    const name = firstName || 'User';
    logger.info(`[EMAIL] 📧 Preparing magic link email for: ${email}`);
    console.log('\n🔗 MAGIC LINK (DEV MODE):');
    console.log(`To: ${email}`);
    console.log(`Name: ${name}`);
    console.log(`Link: ${magicLink}`);
    console.log('\n');
    logger.info(`[EMAIL] ✅ Magic link email sent successfully to: ${email}`);
  }

  async sendWelcome(email: string, firstName?: string): Promise<void> {
    const name = firstName || 'User';
    logger.info(`[EMAIL] 📧 Preparing welcome email for: ${email}`);
    console.log(`✅ Welcome to Circles, ${name}!\n`);
    logger.info(`[EMAIL] ✅ Welcome email sent successfully to: ${email}`);
  }
}

// Select email service based on configuration
function selectEmailService(): EmailServiceInterface {
  // If explicitly set, use the chosen provider
  if (env.emailProvider === 'resend' && env.resendApiKey) {
    logger.info('📧 Using Resend as email provider');
    return new ResendEmailService();
  }

  if (env.emailProvider === 'aws-ses' && env.awsAccessKeyId && env.awsSecretAccessKey) {
    logger.info('📧 Using AWS SES as email provider');
    return new AwsSesEmailService();
  }

  // Auto-detect: Resend if API key is provided
  if (env.resendApiKey) {
    logger.info('📧 Using Resend as email provider (auto-detected)');
    return new ResendEmailService();
  }

  // Fallback to AWS SES in production
  if (env.nodeEnv === 'production' && env.awsAccessKeyId && env.awsSecretAccessKey) {
    logger.info('📧 Using AWS SES as email provider (production fallback)');
    return new AwsSesEmailService();
  }

  // Development: Console logging
  logger.info('📧 Using Dev email service (console logging)');
  return new DevEmailService();
}

const emailService = selectEmailService();

export { emailService };
