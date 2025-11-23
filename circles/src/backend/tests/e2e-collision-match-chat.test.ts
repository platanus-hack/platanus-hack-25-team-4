import { beforeEach, describe, expect, it, vi } from 'vitest';

import { COLLISION_CONFIG } from '../config/collision.config.js';
import { AgentMatchService, type MissionResult } from '../services/agent-match-service.js';
import { CollisionDetectionService } from '../services/collision-detection-service.js';

// In-memory stores shared by mocked Prisma/Redis
type UserStoreItem = {
  id: string;
  centerLat: number | null;
  centerLon: number | null;
};

type CircleStoreItem = {
  id: string;
  userId: string;
  status: string;
  radiusMeters: number;
  objective: string;
  expiresAt: Date;
  startAt: Date;
  createdAt: Date;
};

type CollisionEventStoreItem = {
  id: string;
  circle1Id: string;
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distanceMeters: number;
  firstSeenAt: Date;
  detectedAt: Date;
  status: string;
};

type MissionStoreItem = {
  id: string;
  ownerUserId: string;
  visitorUserId: string;
  ownerCircleId: string;
  visitorCircleId: string;
  collisionEventId: string | null;
  status: string;
  attemptNumber: number;
  transcript: unknown | null;
  judgeDecision: unknown | null;
  failureReason: string | null;
  completedAt: Date | null;
  startedAt: Date | null;
};

type MatchStoreItem = {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  primaryCircleId: string;
  secondaryCircleId: string;
  type: string;
  worthItScore: number;
  status: string;
  explanationSummary: string | null;
  collisionEventId: string | null;
  createdAt: Date;
  updatedAt: Date;
};

type ChatStoreItem = {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  createdAt: Date;
};

const users: UserStoreItem[] = [];

const circles: CircleStoreItem[] = [];

const collisionEvents: CollisionEventStoreItem[] = [];

const missions: MissionStoreItem[] = [];
const matches: MatchStoreItem[] = [];
const chats: ChatStoreItem[] = [];

const redisHashes = new Map<string, Record<string, string>>();
const redisStrings = new Map<string, string>();
const redisSortedSets = new Map<
  string,
  Array<{ score: number; value: string }>
>();
const redisExpires = new Map<string, number>();

// Prisma mock that supports both collision detection and agent matching flows
vi.mock('../lib/prisma.js', () => {
  const prisma = {
    circle: {
      findFirst: vi.fn(
        async ({
          where,
          orderBy,
        }: {
          where?: {
            userId?: string;
            status?: string;
            expiresAt?: { gt?: Date };
            startAt?: { lte?: Date };
          };
          orderBy?: Record<string, string>;
        }) => {
          let filtered = circles.filter((c) => {
            if (where?.userId && c.userId !== where.userId) return false;
            if (where?.status && c.status !== where.status) return false;
            if (where?.expiresAt?.gt && c.expiresAt <= where.expiresAt.gt)
              return false;
            if (where?.startAt?.lte && c.startAt > where.startAt.lte)
              return false;
            return true;
          });

          if (orderBy?.createdAt === 'desc') {
            filtered = filtered.sort(
              (a, b) => b.createdAt.getTime() - a.createdAt.getTime(),
            );
          }

          return filtered[0] || null;
        },
      ),
    },
    collisionEvent: {
      create: vi.fn(
        async ({
          data,
        }: {
          data: {
            circle1Id: string;
            circle2Id: string;
            user1Id: string;
            user2Id: string;
            distanceMeters: number;
            firstSeenAt: Date;
            status: string;
          };
        }) => {
          const event = {
            id: `collision-event-${collisionEvents.length + 1}`,
            ...data,
            detectedAt: data.firstSeenAt,
          };
          collisionEvents.push(event);
          return event;
        },
      ),
      update: vi.fn(
        async ({
          where,
          data,
        }: {
          where: {
            unique_collision_pair?: { circle1Id: string; circle2Id: string };
          };
          data: Record<string, unknown>;
        }) => {
          const { circle1Id, circle2Id } = where.unique_collision_pair || {};
          const event = collisionEvents.find(
            (e) => e.circle1Id === circle1Id && e.circle2Id === circle2Id,
          );
          if (!event) {
            throw new Error('CollisionEvent not found');
          }
          Object.assign(event, data);
          return event;
        },
      ),
      findUnique: vi.fn(
        async ({
          where,
        }: {
          where: { unique_collision_pair: { circle1Id: string; circle2Id: string } };
        }) => {
          const { circle1Id, circle2Id } = where.unique_collision_pair;
          return (
            collisionEvents.find(
              (e) => e.circle1Id === circle1Id && e.circle2Id === circle2Id,
            ) || null
          );
        },
      ),
    },
    interviewMission: {
      create: vi.fn(async ({ data }: { data: Partial<MissionStoreItem> }) => {
        const mission: MissionStoreItem = {
          id: `mission-${missions.length + 1}`,
          transcript: null,
          judgeDecision: null,
          failureReason: null,
          completedAt: null,
          startedAt: null,
          // sensible defaults – tests override the fields they care about
          ownerUserId: '',
          visitorUserId: '',
          ownerCircleId: '',
          visitorCircleId: '',
          collisionEventId: null,
          status: 'pending',
          attemptNumber: 1,
          ...data,
        };
        missions.push(mission);
        return mission;
      }),
      findUnique: vi.fn(async ({ where }: { where: { id: string } }) => {
        return missions.find((mission) => mission.id === where.id) ?? null;
      }),
      update: vi.fn(
        async ({
          where,
          data,
        }: {
          where: { id: string };
          data: Partial<MissionStoreItem>;
        }) => {
          const mission = missions.find((m) => m.id === where.id);
          if (!mission) {
            throw new Error('Mission not found');
          }
          Object.assign(mission, data);
          return mission;
        },
      ),
    },
    match: {
      create: vi.fn(async ({ data }: { data: Partial<MatchStoreItem> }) => {
        const match: MatchStoreItem = {
          id: `match-${matches.length + 1}`,
          primaryUserId: '',
          secondaryUserId: '',
          primaryCircleId: '',
          secondaryCircleId: '',
          type: 'match',
          worthItScore: 0.0,
          status: 'pending_accept',
          explanationSummary: null,
          collisionEventId: null,
          createdAt: new Date(),
          updatedAt: new Date(),
          ...data,
        };
        matches.push(match);
        return match;
      }),
      findFirst: vi.fn(
        async ({
          where,
        }: {
          where: { OR?: Array<{ primaryUserId: string; secondaryUserId: string }> };
        }) => {
          const orConditions = where.OR;
          if (!orConditions) {
            return null;
          }
          return (
            matches.find((m: MatchStoreItem) =>
              orConditions.some(
                (condition: { primaryUserId: string; secondaryUserId: string }) =>
                  m.primaryUserId === condition.primaryUserId &&
                  m.secondaryUserId === condition.secondaryUserId,
              ),
            ) ?? null
          );
        },
      ),
      update: vi.fn(
        async ({
          where,
          data,
        }: {
          where: { id: string };
          data: Partial<MatchStoreItem>;
        }) => {
          const match = matches.find((m: MatchStoreItem) => m.id === where.id);
          if (!match) {
            throw new Error('Match not found');
          }
          Object.assign(match, data);
          return match;
        },
      ),
    },
    chat: {
      create: vi.fn(
        async ({
          data,
        }: {
          data: Omit<ChatStoreItem, 'id' | 'createdAt'>;
        }) => {
          const chat: ChatStoreItem = {
          id: `chat-${chats.length + 1}`,
          createdAt: new Date(),
          ...data,
          };
          chats.push(chat);
          return chat;
        },
      ),
      findFirst: vi.fn(
        async ({
          where,
        }: {
          where: { OR?: Array<{ primaryUserId: string; secondaryUserId: string }> };
        }) => {
          const orConditions = where.OR;
          if (!orConditions) {
            return null;
          }
          return (
            chats.find((c: ChatStoreItem) =>
              orConditions.some(
                (condition: { primaryUserId: string; secondaryUserId: string }) =>
                  c.primaryUserId === condition.primaryUserId &&
                  c.secondaryUserId === condition.secondaryUserId,
              ),
            ) ?? null
          );
        },
      ),
    },
    $transaction: vi.fn(
      async (
        callback: (tx: typeof prisma) => Promise<unknown> | unknown,
      ) => callback(prisma),
    ),
    $queryRaw: vi.fn(async (_query: unknown, ...params: unknown[]) => {
      // Mock PostGIS: return circles for other users within radius of the querying user
      const userIdParam = params.find(
        (p) => typeof p === 'string' && p.startsWith('user-'),
      );
      const userId = typeof userIdParam === 'string' ? userIdParam : undefined;

      const now = new Date();
      return circles
        .filter((c) => {
          if (!userId) return false;
          if (c.userId === userId) return false;
          return c.status === 'active' && c.expiresAt > now && c.startAt <= now;
        })
        .map((c) => {
          const user = users.find((u) => u.id === c.userId);
          if (!user || user.centerLat === null || user.centerLon === null) {
            return null;
          }

          // Simple distance mock: always within radius (scaled random)
          const distance = Math.random() * c.radiusMeters * 0.8;

          return {
            id: c.id,
            userId: c.userId,
            radiusMeters: c.radiusMeters,
            objective: c.objective,
            distance_meters: distance,
          };
        })
        .filter(Boolean)
        .slice(0, COLLISION_CONFIG.SPATIAL_INDEX_SEARCH_LIMIT);
    }),
  };

  return { prisma };
});

// Redis mock that supports collision stability + cooldowns + mission locks
vi.mock('../infrastructure/redis.js', () => {
  const client = {
    hgetall: vi.fn(async (key: string) => {
      return redisHashes.get(key) ?? {};
    }),
    hset: vi.fn(
      async (
        key: string,
        data: Record<string, unknown> | string,
        value?: unknown,
      ) => {
        const existing = redisHashes.get(key) ?? {};
        if (typeof data === 'string') {
          // hset(key, field, value)
          redisHashes.set(key, { ...existing, [data]: String(value) });
        } else {
          // hset(key, { field1: value1, ... })
          const stringified: Record<string, string> = {};
          for (const [k, v] of Object.entries(data)) {
            stringified[k] = String(v);
          }
          redisHashes.set(key, { ...existing, ...stringified });
        }
        return 1;
      },
    ),
    set: vi.fn(
      async (
        key: string,
        value: string,
        mode?: string,
        _ttlSeconds?: number,
        nxFlag?: string,
      ) => {
        if (mode === 'EX' && nxFlag === 'NX') {
          if (redisStrings.has(key)) {
            return null; // lock already held
          }
          redisStrings.set(key, String(value));
          return 'OK';
        }
        redisStrings.set(key, String(value));
        return 'OK';
      },
    ),
    del: vi.fn(async (key: string) => {
      const hashDeleted = redisHashes.delete(key);
      const strDeleted = redisStrings.delete(key);
      const sortedDeleted = redisSortedSets.delete(key);
      return hashDeleted || strDeleted || sortedDeleted ? 1 : 0;
    }),
    expire: vi.fn(async (key: string, seconds: number) => {
      redisExpires.set(key, Date.now() + seconds * 1000);
      return 1;
    }),
    zadd: vi.fn(async (key: string, score: number, value: string) => {
      const set = redisSortedSets.get(key) ?? [];
      set.push({ score, value });
      redisSortedSets.set(key, set);
      return 1;
    }),
  };

  return {
    getRedisClient: () => client,
  };
});

describe('E2E: collision → missions → mutual match and chat', () => {
  let collisionService: CollisionDetectionService;
  let matchService: AgentMatchService;

  beforeEach(() => {
    users.length = 0;
    circles.length = 0;
    collisionEvents.length = 0;
    missions.length = 0;
    matches.length = 0;
    chats.length = 0;
    redisHashes.clear();
    redisStrings.clear();
    redisSortedSets.clear();
    redisExpires.clear();
    vi.clearAllMocks();

    collisionService = new CollisionDetectionService();
    matchService = new AgentMatchService();
  });

  it('runs a full flow for two users from collision to mutual match and chat', async () => {
    const now = Date.now();

    // Two users with positions
    users.push(
      { id: 'user-1', centerLat: 10.0, centerLon: 10.0 },
      { id: 'user-2', centerLat: 10.001, centerLon: 10.001 },
    );

    // Each user has an active circle with an objective
    circles.push(
      {
        id: 'circle-1',
        userId: 'user-1',
        status: 'active',
        radiusMeters: 500,
        objective: 'Coffee meetup',
        expiresAt: new Date(now + 60 * 60 * 1000),
        startAt: new Date(now - 60 * 60 * 1000),
        createdAt: new Date(now - 5000),
      },
      {
        id: 'circle-2',
        userId: 'user-2',
        status: 'active',
        radiusMeters: 500,
        objective: 'Developer networking',
        expiresAt: new Date(now + 60 * 60 * 1000),
        startAt: new Date(now - 60 * 60 * 1000),
        createdAt: new Date(now),
      },
    );

    // Step 1: visitor user-1 moves near user-2 → detect collision(s)
    const collisionsFromUser1 = await collisionService.detectCollisionsForUser(
      'user-1',
      10.001,
      10.001,
    );

    expect(collisionsFromUser1.length).toBeGreaterThan(0);
    const collision1 = collisionsFromUser1.find(
      (c) => c.user2Id === 'user-2',
    );
    expect(collision1).toBeDefined();
    if (!collision1) {
      throw new Error('Expected collision from user-1 to user-2');
    }

    // Step 2: create a mission for this collision (user-1 → user-2)
    const mission1 = await matchService.createMissionForCollision(collision1);

    expect(mission1).not.toBeNull();
    if (!mission1) {
      throw new Error('Expected mission to be created for first collision');
    }
    expect(missions).toHaveLength(1);
    expect(missions[0].ownerUserId).toBe('user-1');
    expect(missions[0].visitorUserId).toBe('user-2');

    // Step 3: first mission succeeds and creates a pending match
    const result1: MissionResult = {
      success: true,
      matchMade: true,
      transcript: JSON.stringify({ messages: [{ role: 'interviewer', content: 'great fit' }] }),
      judgeDecision: { reason: 'great fit', confidence: 0.9 },
    };

    const matchAfterFirstMission = await matchService.handleMissionResult(
      mission1.id,
      result1,
    );

    expect(matchAfterFirstMission).not.toBeNull();
    expect(matches).toHaveLength(1);
    expect(matches[0].status).toBe('pending_accept');

    // No chat yet on one-sided match
    expect(chats).toHaveLength(0);

    // Simulate time passing: clear in-flight mission locks and cooldowns
    // so that a new mission can be created for the same user pair.
    redisStrings.clear();
    redisHashes.clear();

    // Step 4: visitor user-2 moves near user-1 → second collision and mission
    const collisionsFromUser2 = await collisionService.detectCollisionsForUser(
      'user-2',
      10.0,
      10.0,
    );

    expect(collisionsFromUser2.length).toBeGreaterThan(0);
    const collision2 = collisionsFromUser2.find(
      (c) => c.user2Id === 'user-1',
    );
    expect(collision2).toBeDefined();
    if (!collision2) {
      throw new Error('Expected collision from user-2 to user-1');
    }

    const mission2 = await matchService.createMissionForCollision(collision2);

    expect(mission2).not.toBeNull();
    if (!mission2) {
      throw new Error('Expected mission to be created for second collision');
    }
    expect(missions).toHaveLength(2);

    // Step 5: second mission also succeeds with matchMade=true → mutual match
    const result2: MissionResult = {
      success: true,
      matchMade: true,
      transcript: JSON.stringify({ messages: [{ role: 'interviewer', content: 'mutual yes' }] }),
      judgeDecision: { reason: 'mutual match', confidence: 0.95 },
    };

    const finalMatch = await matchService.handleMissionResult(
      mission2.id,
      result2,
    );

    expect(finalMatch).not.toBeNull();

    // We should now have two active matches (one in each direction)
    expect(matches).toHaveLength(2);
    expect(matches.every((m) => m.status === 'active')).toBe(true);

    // And exactly one chat created for the user pair
    expect(chats).toHaveLength(1);
    const chat = chats[0];
    expect(
      (chat.primaryUserId === 'user-1' && chat.secondaryUserId === 'user-2') ||
        (chat.primaryUserId === 'user-2' && chat.secondaryUserId === 'user-1'),
    ).toBe(true);

    // Sanity-check that collision events were persisted for the pair
    expect(
      collisionEvents.some(
        (e) =>
          ((e.circle1Id === 'circle-1' && e.circle2Id === 'circle-2') ||
            (e.circle1Id === 'circle-2' && e.circle2Id === 'circle-1')) &&
          e.user1Id &&
          e.user2Id,
      ),
    ).toBe(true);
  });
});


