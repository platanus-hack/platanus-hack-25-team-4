import { logger } from '../utils/logger.util.js';

export type EmailOptions = {
  to: string;
  subject: string;
  html: string;
  text?: string;
};

class EmailService {
  /**
   * Send magic link email
   */
  async sendMagicLink(email: string, magicLink: string, firstName?: string): Promise<void> {
    const name = firstName || 'User';

    // TODO: Implement real email sending
    // Options:
    // 1. SendGrid
    // 2. Mailgun
    // 3. AWS SES
    // 4. NodeMailer

    // Example with nodemailer (install: npm install nodemailer):
    // const transporter = nodemailer.createTransport({...});
    // const html = `<div>...</div>`;
    // const text = `...`;
    // await transporter.sendMail({ to: email, subject: 'Your Circles Magic Link', html, text });

    // For development/testing, log the magic link
    logger.info(`📧 Magic link sent to ${email}`);
    console.log('\n🔗 MAGIC LINK (DEV MODE):');
    console.log(`To: ${email}`);
    console.log(`Name: ${name}`);
    console.log(`Link: ${magicLink}`);
    console.log('\n');
  }

  /**
   * Send welcome email
   */
  async sendWelcome(email: string, firstName?: string): Promise<void> {
    const name = firstName || 'User';

    // TODO: Implement real email sending
    // Example with nodemailer:
    // const transporter = nodemailer.createTransport({...});
    // const html = `<h1>Welcome!</h1>`;
    // await transporter.sendMail({ to: email, subject: 'Welcome to Circles!', html });

    logger.info(`📧 Welcome email sent to ${email}`);
    console.log(`✅ Welcome to Circles, ${name}!\n`);
  }
}

export const emailService = new EmailService();
