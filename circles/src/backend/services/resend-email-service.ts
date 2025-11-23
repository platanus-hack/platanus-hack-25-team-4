import { Resend } from 'resend';

import { env } from '../config/env.js';
import { logger } from '../utils/logger.util.js';

export class ResendEmailService {
  private resend: Resend;

  constructor() {
    this.resend = new Resend(env.resendApiKey);
  }

  async sendMagicLink(email: string, magicLink: string, firstName?: string): Promise<void> {
    const name = firstName || 'Usuario';
    const html = `
      <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #5B5FEE 0%, #34D1BF 100%); padding: 20px;">
        <div style="background-color: white; border-radius: 12px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
          <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 15px;">🎯</div>
            <h1 style="color: #5B5FEE; margin: 0; font-size: 28px;">¡Bienvenido a Circles, ${name}!</h1>
          </div>
          
          <p style="color: #525866; font-size: 16px; line-height: 1.8; text-align: center;">
            Estamos muy emocionados de tenerte aquí. Haz clic en el botón de abajo para acceder a tu cuenta o crear una nueva.
          </p>
          
          <div style="text-align: center; margin: 35px 0;">
            <a href="${magicLink}" style="background: linear-gradient(135deg, #5B5FEE 0%, #FF8A3D 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600; display: inline-block; border: none; cursor: pointer; box-shadow: 0 4px 15px rgba(91, 95, 238, 0.4); transition: transform 0.2s ease;">
              ✨ Acceder con Magic Link
            </a>
          </div>
          
          <p style="color: #525866; font-size: 14px; text-align: center; margin-top: 25px;">
            O copia y pega este enlace en tu navegador:
          </p>
          <p style="word-break: break-all; background-color: #F6F7FC; padding: 15px; border-left: 4px solid #5B5FEE; border-radius: 4px; font-size: 12px; color: #1A1A1A; font-family: 'Courier New', monospace; margin: 15px 0;">
            ${magicLink}
          </p>
          
          <div style="background-color: #FFF5E6; border-left: 4px solid #FF8A3D; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p style="color: #FF8A3D; font-size: 13px; margin: 0;">
              ⏱️ Este enlace expirará en 15 minutos por tu seguridad.
            </p>
          </div>
          
          <hr style="border: none; border-top: 2px solid #F6F7FC; margin: 30px 0;">
          
          <p style="color: #525866; font-size: 12px; text-align: center;">
            Si no solicitaste este enlace, puedes ignorar este correo de forma segura.
          </p>
          
          <p style="color: #525866; font-size: 11px; text-align: center; margin-top: 20px;">
            💜 Con cariño, el equipo de Circles<br>
            © 2025 Circles. Todos los derechos reservados.
          </p>
        </div>
      </div>
    `;

    const text = `
¡Bienvenido a Circles, ${name}! 🎯

Estamos muy emocionados de tenerte aquí.

Accede a tu cuenta usando este enlace:
${magicLink}

Este enlace expirará en 15 minutos por tu seguridad.

Si no solicitaste este enlace, puedes ignorar este correo de forma segura.

Con cariño,
El equipo de Circles

© 2025 Circles. Todos los derechos reservados.
    `;

    try {
      const response = await this.resend.emails.send({
        from: env.resendFromEmail,
        to: email,
        subject: '✨ Tu enlace mágico de Circles',
        html,
        text
      });

      if (response.error) {
        logger.error(`No se pudo enviar el enlace mágico a ${email}: ${response.error.message}`);
        throw new Error(`Resend error: ${response.error.message}`);
      }

      logger.info(`📧 Correo de enlace mágico enviado a ${email} (ID de mensaje: ${response.data?.id})`);
      console.log(`✅ Enlace mágico enviado a: ${email}`);
    } catch (error) {
      logger.error(`No se pudo enviar el enlace mágico a ${email}`);
      throw error;
    }
  }

  async sendWelcome(email: string, firstName?: string): Promise<void> {
    const name = firstName || 'Usuario';
    const html = `
      <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #5B5FEE 0%, #34D1BF 100%); padding: 20px;">
        <div style="background-color: white; border-radius: 12px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
          <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 56px; margin-bottom: 15px; animation: bounce 2s infinite;">🚀</div>
            <h1 style="color: #5B5FEE; margin: 0; font-size: 28px;">¡Bienvenido a Circles, ${name}! 🎯</h1>
          </div>
          
          <p style="color: #525866; font-size: 16px; line-height: 1.8; text-align: center;">
            ¡Tu cuenta ha sido creada exitosamente! Ahora es momento de explorar, conectar y descubrir comunidades increíbles que comparten tus intereses.
          </p>
          
          <div style="background-color: #F6F7FC; border-left: 4px solid #5B5FEE; padding: 20px; border-radius: 6px; margin: 25px 0;">
            <p style="color: #5B5FEE; font-size: 14px; font-weight: 600; margin-top: 0;">Lo que puedes hacer ahora:</p>
            <ul style="color: #525866; font-size: 14px; margin: 10px 0; padding-left: 20px;">
              <li>🔍 Explora círculos basados en tus intereses</li>
              <li>👥 Conecta con personas que comparten tus pasiones</li>
              <li>💬 Participa en conversaciones significativas</li>
              <li>🌟 Crea tu propio círculo y sé un líder</li>
            </ul>
          </div>
          
          <p style="color: #525866; font-size: 15px; text-align: center; font-style: italic;">
            ¡Que disfrutes explorando! 🎉
          </p>
          
          <hr style="border: none; border-top: 2px solid #F6F7FC; margin: 30px 0;">
          
          <p style="color: #525866; font-size: 11px; text-align: center;">
            Con 💜 por el equipo de Circles<br>
            © 2025 Circles. Todos los derechos reservados.
          </p>
        </div>
      </div>
    `;

    const text = `
¡Bienvenido a Circles, ${name}! 🎯🚀

¡Tu cuenta ha sido creada exitosamente!

Ahora puedes:
🔍 Explorar círculos basados en tus intereses
👥 Conectar con personas que comparten tus pasiones
💬 Participar en conversaciones significativas
🌟 Crear tu propio círculo y ser un líder

¡Que disfrutes explorando!

Con cariño,
El equipo de Circles

© 2025 Circles. Todos los derechos reservados.
    `;

    try {
      const response = await this.resend.emails.send({
        from: env.resendFromEmail,
        to: email,
        subject: '🎉 ¡Bienvenido a Circles!',
        html,
        text
      });

      if (response.error) {
        logger.error(`No se pudo enviar el correo de bienvenida a ${email}: ${response.error.message}`);
        throw new Error(`Resend error: ${response.error.message}`);
      }

      logger.info(`📧 Correo de bienvenida enviado a ${email} (ID de mensaje: ${response.data?.id})`);
      console.log(`✅ Correo de bienvenida enviado a: ${email}`);
    } catch (error) {
      logger.error(`No se pudo enviar el correo de bienvenida a ${email}`);
      throw error;
    }
  }
}

