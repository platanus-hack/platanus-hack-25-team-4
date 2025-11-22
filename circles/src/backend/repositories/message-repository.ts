import { prisma } from '../lib/prisma.js';
import { Message, CreateMessageInput, UpdateMessageInput, ModerationFlags } from '../types/message.type.js';

/**
 * Type guard to check if an object is valid ModerationFlags
 */
function isModerationFlags(obj: unknown): obj is ModerationFlags {
  return typeof obj === 'object' && obj !== null;
}

/**
 * Repository for Message database operations
 */
export class MessageRepository {
  /**
   * Create a new message
   */
  async create(input: CreateMessageInput): Promise<Message> {
    const message = await prisma.message.create({
      data: {
        chatId: input.chatId,
        senderUserId: input.senderUserId,
        receiverId: input.receiverId,
        content: input.content,
        moderationFlags: input.moderationFlags ?? null
      }
    });

    return this.mapToMessage(message);
  }

  /**
   * Get a message by ID
   */
  async findById(id: string): Promise<Message | null> {
    const message = await prisma.message.findUnique({
      where: { id }
    });

    return message ? this.mapToMessage(message) : null;
  }

  /**
   * Get all messages in a chat
   */
  async findByChatId(chatId: string): Promise<Message[]> {
    const messages = await prisma.message.findMany({
      where: { chatId },
      orderBy: {
        createdAt: 'asc'
      }
    });

    return messages.map((msg: {
      id: string;
      chatId: string;
      senderUserId: string;
      receiverId: string;
      content: string;
      moderationFlags: unknown;
      createdAt: Date;
    }): Message => this.mapToMessage(msg));
  }

  /**
   * Get all messages sent by a user
   */
  async findBySenderId(senderUserId: string): Promise<Message[]> {
    const messages = await prisma.message.findMany({
      where: { senderUserId },
      orderBy: {
        createdAt: 'desc'
      }
    });

    return messages.map((msg: {
      id: string;
      chatId: string;
      senderUserId: string;
      receiverId: string;
      content: string;
      moderationFlags: unknown;
      createdAt: Date;
    }): Message => this.mapToMessage(msg));
  }

  /**
   * Get all messages received by a user
   */
  async findByReceiverId(receiverId: string): Promise<Message[]> {
    const messages = await prisma.message.findMany({
      where: { receiverId },
      orderBy: {
        createdAt: 'desc'
      }
    });

    return messages.map((msg: {
      id: string;
      chatId: string;
      senderUserId: string;
      receiverId: string;
      content: string;
      moderationFlags: unknown;
      createdAt: Date;
    }): Message => this.mapToMessage(msg));
  }

  /**
   * Get paginated messages in a chat
   */
  async findByChatIdPaginated(
    chatId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{ messages: Message[]; total: number }> {
    const [messages, total] = await Promise.all([
      prisma.message.findMany({
        where: { chatId },
        skip: offset,
        take: limit,
        orderBy: {
          createdAt: 'asc'
        }
      }),
      prisma.message.count({
        where: { chatId }
      })
    ]);

    return {
      messages: messages.map((msg: {
        id: string;
        chatId: string;
        senderUserId: string;
        receiverId: string;
        content: string;
        moderationFlags: unknown;
        createdAt: Date;
      }): Message => this.mapToMessage(msg)),
      total
    };
  }

  /**
   * Update a message
   */
  async update(id: string, input: UpdateMessageInput): Promise<Message | null> {
    const message = await prisma.message.update({
      where: { id },
      data: input
    });

    return this.mapToMessage(message);
  }

  /**
   * Delete a message
   */
  async delete(id: string): Promise<boolean> {
    try {
      await prisma.message.delete({
        where: { id }
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Map Prisma Message to Message type
   */
  private mapToMessage(message: {
    id: string;
    chatId: string;
    senderUserId: string;
    receiverId: string;
    content: string;
    moderationFlags: unknown;
    createdAt: Date;
  }): Message {
    const moderationFlags = isModerationFlags(message.moderationFlags)
      ? message.moderationFlags
      : null;

    return {
      id: message.id,
      chatId: message.chatId,
      senderUserId: message.senderUserId,
      receiverId: message.receiverId,
      content: message.content,
      moderationFlags,
      createdAt: message.createdAt
    };
  }
}

