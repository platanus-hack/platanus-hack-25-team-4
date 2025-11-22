import { prisma } from '../lib/prisma.js';
import { Chat, CreateChatInput, UpdateChatInput } from '../types/chat.type.js';

/**
 * Repository for Chat database operations
 */
export class ChatRepository {
  /**
   * Create a new chat
   */
  async create(input: CreateChatInput): Promise<Chat> {
    const chat = await prisma.chat.create({
      data: {
        primaryUserId: input.primaryUserId,
        secondaryUserId: input.secondaryUserId,
        matchId: input.matchId ?? null
      }
    });

    return this.mapToChat(chat);
  }

  /**
   * Get a chat by ID
   */
  async findById(id: string): Promise<Chat | null> {
    const chat = await prisma.chat.findUnique({
      where: { id }
    });

    return chat ? this.mapToChat(chat) : null;
  }

  /**
   * Get all chats for a user (as either primary or secondary user)
   */
  async findByUserId(userId: string): Promise<Chat[]> {
    const chats = await prisma.chat.findMany({
      where: {
        OR: [
          { primaryUserId: userId },
          { secondaryUserId: userId }
        ]
      },
      orderBy: {
        createdAt: 'desc'
      }
    });

    return chats.map((chat: {
      id: string;
      primaryUserId: string;
      secondaryUserId: string;
      matchId: string | null;
      createdAt: Date;
    }): Chat => this.mapToChat(chat));
  }

  /**
   * Get a chat between two specific users
   */
  async findBetweenUsers(userId1: string, userId2: string): Promise<Chat | null> {
    const chat = await prisma.chat.findFirst({
      where: {
        OR: [
          {
            primaryUserId: userId1,
            secondaryUserId: userId2
          },
          {
            primaryUserId: userId2,
            secondaryUserId: userId1
          }
        ]
      }
    });

    return chat ? this.mapToChat(chat) : null;
  }

  /**
   * Get all chats (admin only)
   */
  async findAll(): Promise<Chat[]> {
    const chats = await prisma.chat.findMany({
      orderBy: {
        createdAt: 'desc'
      }
    });

    return chats.map((chat: {
      id: string;
      primaryUserId: string;
      secondaryUserId: string;
      matchId: string | null;
      createdAt: Date;
    }): Chat => this.mapToChat(chat));
  }

  /**
   * Update a chat
   */
  async update(id: string, input: UpdateChatInput): Promise<Chat | null> {
    const chat = await prisma.chat.update({
      where: { id },
      data: {
        matchId: input.matchId ?? null
      }
    });

    return this.mapToChat(chat);
  }

  /**
   * Delete a chat
   */
  async delete(id: string): Promise<boolean> {
    try {
      await prisma.chat.delete({
        where: { id }
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Map Prisma Chat to Chat type
   */
  private mapToChat(chat: {
    id: string;
    primaryUserId: string;
    secondaryUserId: string;
    matchId: string | null;
    createdAt: Date;
  }): Chat {
    return {
      id: chat.id,
      primaryUserId: chat.primaryUserId,
      secondaryUserId: chat.secondaryUserId,
      matchId: chat.matchId ? chat.matchId : undefined,
      createdAt: chat.createdAt
    };
  }
}

