export type UserProfile = {
  interests: string[];
  socialStyle?: string;
  boundaries?: string[];
  availability?: string;
};

export type User = {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  passwordHash: string;
  profile: UserProfile;
};

export type PublicUser = Omit<User, 'passwordHash'>;

export type AuthPayload = {
  userId: string;
  email: string;
};
