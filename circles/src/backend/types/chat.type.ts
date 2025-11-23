/**
 * Chat model matching Prisma schema
 */
export type Chat = {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  matchId?: string | null | undefined;
  createdAt: Date;
};

/**
 * Chat creation input
 */
export type CreateChatInput = {
  primaryUserId: string;
  secondaryUserId: string;
  matchId?: string | null | undefined;
};

/**
 * Chat update input
 */
export type UpdateChatInput = Partial<Omit<CreateChatInput, 'primaryUserId' | 'secondaryUserId'>>;

/**
 * Chat with related entities (for detailed responses)
 */
export type ChatWithDetails = Chat & {
  primaryUser?: {
    id: string;
    email: string;
    firstName: string | null;
    lastName: string | null;
  };
  secondaryUser?: {
    id: string;
    email: string;
    firstName: string | null;
    lastName: string | null;
  };
  messages?: Array<{
    id: string;
    content: string;
    createdAt: Date;
    senderUserId: string;
  }>;
};

