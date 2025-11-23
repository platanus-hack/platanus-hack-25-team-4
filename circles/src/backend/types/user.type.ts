/**
 * Single user interest with title and description
 */
export type Interest = {
  title: string;
  description: string;
};

/**
 * User profile structured data - compatible with Prisma JSON serialization
 */
export type UserProfile = {
  bio?: string;
  interests?: Interest[];
  profileCompleted?: boolean;
  socialStyle?: string;
  boundaries?: string[];
  availability?: string;
};

/**
 * User model matching Prisma schema
 */
export type User = {
  id: string;
  email: string;
  firstName?: string | null;
  lastName?: string | null;
  passwordHash?: string | null; // Optional for magic link auth
  profile: UserProfile | null;
  centerLat?: number | null; // User's current latitude
  centerLon?: number | null; // User's current longitude
  createdAt: Date;
  updatedAt: Date;
};

/**
 * User without sensitive data
 */
export type PublicUser = Omit<User, 'passwordHash'>;

/**
 * User creation input
 */
export type CreateUserInput = {
  email: string;
  firstName?: string;
  lastName?: string;
  passwordHash?: string; // Optional for magic link auth
  profile?: UserProfile;
  centerLat?: number;
  centerLon?: number;
};

/**
 * User update input
 */
export type UpdateUserInput = Partial<Omit<CreateUserInput, 'email'>> & {
  centerLat?: number | null;
  centerLon?: number | null;
};

/**
 * Authentication payload
 */
export type AuthPayload = {
  userId: string;
  email: string;
};
