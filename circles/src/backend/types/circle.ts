export type CircleStatus = 'active' | 'paused' | 'expired';

export type Circle = {
  id: string;
  userId: string;
  objectiveText: string;
  centerLat: number;
  centerLon: number;
  radiusMeters: number;
  startAt: Date;
  expiresAt: Date;
  status: CircleStatus;
  createdAt: Date;
  updatedAt: Date;
};
