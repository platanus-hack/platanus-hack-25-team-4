import { prisma } from '../lib/prisma.js';
import { ChatRepository } from '../repositories/chat-repository.js';
import { MessageRepository } from '../repositories/message-repository.js';
import { AppError } from '../types/app-error.type.js';
import { Chat, CreateChatInput, ChatWithDetails } from '../types/chat.type.js';
import { Message } from '../types/message.type.js';

/**
 * Service for chat operations
 */
export class ChatService {
  private readonly chatRepository: ChatRepository;
  private readonly messageRepository: MessageRepository;

  constructor() {
    this.chatRepository = new ChatRepository();
    this.messageRepository = new MessageRepository();
  }

  /**
   * Create a new chat between two users
   */
  async create(input: CreateChatInput): Promise<Chat> {
    // Check if chat already exists between these users
    const existing = await this.chatRepository.findBetweenUsers(
      input.primaryUserId,
      input.secondaryUserId
    );

    if (existing) {
      throw new AppError('Chat already exists between these users', 409);
    }

    return this.chatRepository.create(input);
  }

  /**
   * Get a chat by ID with full details
   */
  async getById(id: string): Promise<ChatWithDetails | null> {
    const chat = await this.chatRepository.findById(id);
    if (!chat) return null;

    return this.enrichChatWithDetails(chat);
  }

  /**
   * List all chats for a user with latest message preview
   */
  async listByUserId(userId: string): Promise<(ChatWithDetails & { latestMessage: Message | null })[]> {
    const chats = await this.chatRepository.findByUserId(userId);

    const enriched: (ChatWithDetails & { latestMessage: Message | null })[] = await Promise.all(
      chats.map(async (chat) => {
        const detailed = await this.enrichChatWithDetails(chat);

        // Get latest message
        const messages = await this.messageRepository.findByChatId(chat.id);
        const latestMessage: Message | null = messages.length > 0 ? messages[messages.length - 1]! : null;

        return {
          ...detailed,
          latestMessage
        };
      })
    );

    return enriched;
  }

  /**
   * Get chat between two users
   */
  async getBetweenUsers(userId1: string, userId2: string): Promise<ChatWithDetails | null> {
    const chat = await this.chatRepository.findBetweenUsers(userId1, userId2);
    if (!chat) return null;

    return this.enrichChatWithDetails(chat);
  }

  /**
   * Get messages in a chat
   */
  async getMessages(chatId: string, limit: number = 50, offset: number = 0): Promise<{
    messages: Message[];
    total: number;
  }> {
    // Verify chat exists
    const chat = await this.chatRepository.findById(chatId);
    if (!chat) {
      throw new AppError('Chat not found', 404);
    }

    return this.messageRepository.findByChatIdPaginated(chatId, limit, offset);
  }

  /**
   * Delete a chat (only if user is one of the participants)
   */
  async delete(id: string, userId: string): Promise<boolean> {
    const chat = await this.chatRepository.findById(id);
    if (!chat) {
      throw new AppError('Chat not found', 404);
    }

    const isParticipant = chat.primaryUserId === userId || chat.secondaryUserId === userId;
    if (!isParticipant) {
      throw new AppError('Not authorized to delete this chat', 403);
    }

    return this.chatRepository.delete(id);
  }

  /**
   * Enrich chat with user details
   */
  private async enrichChatWithDetails(chat: Chat): Promise<ChatWithDetails> {
    const [primaryUser, secondaryUser] = await Promise.all([
      prisma.user.findUnique({
        where: { id: chat.primaryUserId },
        select: {
          id: true,
          email: true,
          firstName: true,
          lastName: true
        }
      }),
      prisma.user.findUnique({
        where: { id: chat.secondaryUserId },
        select: {
          id: true,
          email: true,
          firstName: true,
          lastName: true
        }
      })
    ]);

    return {
      ...chat,
      primaryUser: primaryUser ?? undefined,
      secondaryUser: secondaryUser ?? undefined
    };
  }
}
