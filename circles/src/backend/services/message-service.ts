import { prisma } from '../lib/prisma.js';
import { ChatRepository } from '../repositories/chat-repository.js';
import { MessageRepository } from '../repositories/message-repository.js';
import { AppError } from '../types/app-error.type.js';
import { Message, CreateMessageInput, MessageWithDetails } from '../types/message.type.js';

/**
 * Service for message operations
 */
export class MessageService {
  private readonly messageRepository: MessageRepository;
  private readonly chatRepository: ChatRepository;

  constructor() {
    this.messageRepository = new MessageRepository();
    this.chatRepository = new ChatRepository();
  }

  /**
   * Create a new message in a chat
   */
  async create(input: CreateMessageInput, userId: string): Promise<Message> {
    // Verify user is the sender
    if (input.senderUserId !== userId) {
      throw new AppError('Not authorized to send this message', 403);
    }

    // Verify chat exists
    const chat = await this.chatRepository.findById(input.chatId);
    if (!chat) {
      throw new AppError('Chat not found', 404);
    }

    // Verify users are participants in the chat
    const isParticipant =
      chat.primaryUserId === input.senderUserId || chat.secondaryUserId === input.senderUserId;
    if (!isParticipant) {
      throw new AppError('Not authorized to send messages in this chat', 403);
    }

    // Verify receiver is the other participant
    const otherParticipant =
      chat.primaryUserId === input.senderUserId ? chat.secondaryUserId : chat.primaryUserId;
    if (input.receiverId !== otherParticipant) {
      throw new AppError('Invalid receiver for this chat', 400);
    }

    // Verify sender and receiver exist
    const [sender, receiver] = await Promise.all([
      prisma.user.findUnique({ where: { id: input.senderUserId } }),
      prisma.user.findUnique({ where: { id: input.receiverId } })
    ]);

    if (!sender || !receiver) {
      throw new AppError('Sender or receiver not found', 404);
    }

    return this.messageRepository.create(input);
  }

  /**
   * Get a message by ID
   */
  async getById(id: string, userId: string): Promise<MessageWithDetails | null> {
    const message = await this.messageRepository.findById(id);
    if (!message) return null;

    // Verify user is authorized (sender or receiver)
    const isAuthorized = message.senderUserId === userId || message.receiverId === userId;
    if (!isAuthorized) {
      throw new AppError('Not authorized to view this message', 403);
    }

    return this.enrichMessageWithDetails(message);
  }

  /**
   * Get all messages in a chat (paginated)
   */
  async getByChatId(
    chatId: string,
    userId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{
    messages: MessageWithDetails[];
    total: number;
  }> {
    // Verify chat exists and user is a participant
    const chat = await this.chatRepository.findById(chatId);
    if (!chat) {
      throw new AppError('Chat not found', 404);
    }

    const isParticipant = chat.primaryUserId === userId || chat.secondaryUserId === userId;
    if (!isParticipant) {
      throw new AppError('Not authorized to view this chat', 403);
    }

    const result = await this.messageRepository.findByChatIdPaginated(chatId, limit, offset);

    const enrichedMessages = await Promise.all(
      result.messages.map(msg => this.enrichMessageWithDetails(msg))
    );

    return {
      messages: enrichedMessages,
      total: result.total
    };
  }

  /**
   * Delete a message (only sender can delete)
   */
  async delete(id: string, userId: string): Promise<boolean> {
    const message = await this.messageRepository.findById(id);
    if (!message) {
      throw new AppError('Message not found', 404);
    }

    // Only sender can delete
    if (message.senderUserId !== userId) {
      throw new AppError('Not authorized to delete this message', 403);
    }

    return this.messageRepository.delete(id);
  }

  /**
   * Enrich message with user details
   */
  private async enrichMessageWithDetails(message: Message): Promise<MessageWithDetails> {
    const [sender, receiver, chat] = await Promise.all([
      prisma.user.findUnique({
        where: { id: message.senderUserId },
        select: {
          id: true,
          email: true,
          firstName: true,
          lastName: true
        }
      }),
      prisma.user.findUnique({
        where: { id: message.receiverId },
        select: {
          id: true,
          email: true,
          firstName: true,
          lastName: true
        }
      }),
      prisma.chat.findUnique({
        where: { id: message.chatId },
        select: { id: true }
      })
    ]);

    const result: MessageWithDetails = {
      ...message,
    };

    if (chat) {
      result.chat = chat;
    }
    if (sender) {
      result.sender = sender;
    }
    if (receiver) {
      result.receiver = receiver;
    }

    return result;
  }
}
