/**
 * Agent persona safety rules
 */
export type SafetyRules = {
  [key: string]: unknown;
};

/**
 * Agent persona model matching Prisma schema
 */
export type AgentPersona = {
  userId: string;
  safetyRules: SafetyRules | null;
  createdAt: Date;
  updatedAt: Date;
};

/**
 * Agent persona creation input
 */
export type CreateAgentPersonaInput = {
  userId: string;
  safetyRules?: SafetyRules;
};

/**
 * Agent persona update input
 */
export type UpdateAgentPersonaInput = Partial<Omit<CreateAgentPersonaInput, 'userId'>>;

/**
 * Agent persona with user details (for responses)
 */
export type AgentPersonaWithUser = AgentPersona & {
  user?: {
    id: string;
    email: string;
    firstName?: string | null;
    lastName?: string | null;
  };
};

