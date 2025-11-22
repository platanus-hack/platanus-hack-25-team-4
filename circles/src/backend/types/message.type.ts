/**
 * Message moderation flags - compatible with Prisma JSON serialization
 */
export type ModerationFlags = Record<string, string | number | boolean | null | undefined>;

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
  chat: {
    id: string;
  } | undefined;
  sender: {
    id: string;
    email: string;
    firstName: string | null;
    lastName: string | null;
  } | undefined;
  receiver: {
    id: string;
    email: string;
    firstName: string | null;
    lastName: string | null;
  } | undefined;
};

