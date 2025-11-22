import { Router, type Request, type Response } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import { ChatService } from '../services/chat-service.js';
import { MessageService } from '../services/message-service.js';
import { asyncHandler } from '../utils/async-handler.util.js';

export const chatsRouter = Router();

// Service instances
const chatService = new ChatService();
const messageService = new MessageService();

// Schemas
const createChatSchema = z.object({
  primaryUserId: z.string().uuid(),
  secondaryUserId: z.string().uuid(),
  matchId: z.string().uuid().nullable().optional()
});

const createMessageSchema = z.object({
  content: z.string().min(1).max(5000),
  receiverId: z.string().uuid()
});

// Middleware
chatsRouter.use(requireAuth);

// ============================================================================
// CHAT CONTROLLER - CRUD Operations
// ============================================================================

/**
 * R (Read): GET /api/chats
 * List all chats for the authenticated user
 */
chatsRouter.get(
  '/chats',
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const chats = await chatService.listByUserId(userId);
    res.json({
      data: chats,
      count: chats.length
    });
  })
);

/**
 * C (Create): POST /api/chats
 * Create a new chat between two users
 */
chatsRouter.post(
  '/chats',
  validateBody(createChatSchema),
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const bodyData = createChatSchema.parse(req.body);

    // Verify user is one of the participants
    if (bodyData.primaryUserId !== userId && bodyData.secondaryUserId !== userId) {
      res.status(403).json({ error: 'Not authorized to create this chat' });
      return;
    }

    const createInput = {
      primaryUserId: bodyData.primaryUserId,
      secondaryUserId: bodyData.secondaryUserId,
      matchId: bodyData.matchId ?? undefined
    };

    const chat = await chatService.create(createInput);
    res.status(201).json(chat);
  })
);

/**
 * R (Read): GET /api/chats/:chatId
 * Get a specific chat with details
 */
chatsRouter.get(
  '/chats/:chatId',
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { chatId } = req.params;
    if (typeof chatId !== 'string') {
      res.status(400).json({ error: 'Invalid chat ID' });
      return;
    }

    const chat = await chatService.getById(chatId);

    if (!chat) {
      res.status(404).json({ error: 'Chat not found' });
      return;
    }

    // Verify user is a participant
    const isParticipant =
      chat.primaryUserId === userId || chat.secondaryUserId === userId;
    if (!isParticipant) {
      res.status(403).json({ error: 'Not authorized to view this chat' });
      return;
    }

    res.json(chat);
  })
);

/**
 * D (Delete): DELETE /api/chats/:chatId
 * Delete a chat (only participants can delete)
 */
chatsRouter.delete(
  '/chats/:chatId',
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { chatId } = req.params;
    if (typeof chatId !== 'string') {
      res.status(400).json({ error: 'Invalid chat ID' });
      return;
    }

    await chatService.delete(chatId, userId);
    res.status(204).send();
  })
);

// ============================================================================
// MESSAGE CONTROLLER - Nested CRUD Operations (inside chats)
// ============================================================================

/**
 * R (Read): GET /api/chats/:chatId/messages
 * List all messages in a chat (paginated)
 */
chatsRouter.get(
  '/chats/:chatId/messages',
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { chatId } = req.params;
    if (typeof chatId !== 'string') {
      res.status(400).json({ error: 'Invalid chat ID' });
      return;
    }

    const limitParam = typeof req.query.limit === 'string' ? parseInt(req.query.limit) : 50;
    const offsetParam = typeof req.query.offset === 'string' ? parseInt(req.query.offset) : 0;
    const limit = Math.min(limitParam || 50, 100);
    const offset = offsetParam || 0;

    const result = await messageService.getByChatId(chatId, userId, limit, offset);
    res.json({
      data: result.messages,
      total: result.total,
      limit,
      offset
    });
  })
);

/**
 * C (Create): POST /api/chats/:chatId/messages
 * Create a new message in a chat
 */
chatsRouter.post(
  '/chats/:chatId/messages',
  validateBody(createMessageSchema),
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { chatId } = req.params;
    if (typeof chatId !== 'string') {
      res.status(400).json({ error: 'Invalid chat ID' });
      return;
    }

    const bodyData = createMessageSchema.parse(req.body);

    const messageInput = {
      chatId,
      senderUserId: userId,
      receiverId: bodyData.receiverId,
      content: bodyData.content
    };

    const message = await messageService.create(messageInput, userId);
    res.status(201).json(message);
  })
);

/**
 * R (Read): GET /api/chats/:chatId/messages/:messageId
 * Get a specific message
 */
chatsRouter.get(
  '/chats/:chatId/messages/:messageId',
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { messageId } = req.params;
    if (typeof messageId !== 'string') {
      res.status(400).json({ error: 'Invalid message ID' });
      return;
    }

    const message = await messageService.getById(messageId, userId);

    if (!message) {
      res.status(404).json({ error: 'Message not found' });
      return;
    }

    res.json(message);
  })
);

/**
 * D (Delete): DELETE /api/chats/:chatId/messages/:messageId
 * Delete a message (only sender can delete)
 */
chatsRouter.delete(
  '/chats/:chatId/messages/:messageId',
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { messageId } = req.params;
    if (typeof messageId !== 'string') {
      res.status(400).json({ error: 'Invalid message ID' });
      return;
    }

    await messageService.delete(messageId, userId);
    res.status(204).send();
  })
);
