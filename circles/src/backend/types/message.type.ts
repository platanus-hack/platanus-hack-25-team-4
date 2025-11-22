/**
 * Message moderation flags
 */
export type ModerationFlags = {
  flagged?: boolean;
  reason?: string;
  [key: string]: unknown;
};

/**
 * Message model matching Prisma schema
 */
export type Message = {
  id: string;
  chatId: string;
  senderUserId: string;
  receiverId: string;
  content: string;
  moderationFlags: ModerationFlags | null;
  createdAt: Date;
};

/**
 * Message creation input
 */
export type CreateMessageInput = {
  chatId: string;
  senderUserId: string;
  receiverId: string;
  content: string;
  moderationFlags?: ModerationFlags;
};

/**
 * Message update input (limited fields can be updated)
 */
export type UpdateMessageInput = Partial<Pick<CreateMessageInput, 'moderationFlags'>>;

/**
 * Message with related entities (for detailed responses)
 */
export type MessageWithDetails = Message & {
  chat?: {
    id: string;
  };
  sender?: {
    id: string;
    email: string;
    firstName?: string | null;
    lastName?: string | null;
  };
  receiver?: {
    id: string;
    email: string;
    firstName?: string | null;
    lastName?: string | null;
  };
};

