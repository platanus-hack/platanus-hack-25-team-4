import { COLLISION_CONFIG } from '../config/collision.config.js';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock missionQueue module
vi.mock('../interview/missionQueue.js', () => ({
  enqueueMission: vi.fn().mockResolvedValue('test-job-id'),
  missionQueue: {}
}));

// Type definitions for mock data structures
interface MockMission {
  id: string;
  ownerUserId: string;
  visitorUserId: string;
  ownerCircleId: string;
  visitorCircleId: string;
  collisionEventId: string;
  status: string;
  transcript?: unknown;
  judgeDecision?: unknown;
  failureReason?: string | null;
  completedAt?: Date | null;
  startedAt?: Date | null;
  attemptNumber: number;
}

interface MockCollisionEvent {
  id: string;
  circle1Id: string;
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distanceMeters: number;
  status: string;
  missionId?: string;
}

interface MockMatch {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  primaryCircleId: string;
  secondaryCircleId: string;
  type: string;
  worthItScore: number;
  status: string;
  createdAt: Date;
  updatedAt: Date;
}

interface MockChat {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  createdAt: Date;
}

interface MockCircle {
  userId: string;
  status: string;
  expiresAt: Date;
}

// In-memory stores used by Prisma and Redis mocks
const missions: MockMission[] = [];
const collisionEvents: MockCollisionEvent[] = [];
const matches: MockMatch[] = [];
const chats: MockChat[] = [];
const circles: MockCircle[] = [];

const redisHashes = new Map<string, Record<string, string>>();
const redisStrings = new Map<string, string>();

vi.mock('../lib/prisma.js', () => {
  const prisma = {
    interviewMission: {
      create: vi.fn(async ({ data }: { data: Partial<MockMission> }) => {
        const mission: MockMission = {
          id: `mission-${missions.length + 1}`,
          transcript: null,
          judgeDecision: null,
          failureReason: null,
          completedAt: null,
          startedAt: null,
          attemptNumber: 1,
          ownerUserId: '',
          visitorUserId: '',
          ownerCircleId: '',
          visitorCircleId: '',
          collisionEventId: '',
          status: 'pending',
          ...data
        };
        missions.push(mission);
        return mission;
      }),
      findUnique: vi.fn(async ({ where }: { where: { id: string } }) => {
        return missions.find((mission) => mission.id === where.id) ?? null;
      }),
      update: vi.fn(
        async ({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
          const mission = missions.find((m) => m.id === where.id);
          if (!mission) {
            throw new Error('Mission not found');
          }
          Object.assign(mission, data);
          return mission;
        }
      )
    },
    collisionEvent: {
      update: vi.fn(
        async ({
          where,
          data
        }: {
          where: { unique_collision_pair: { circle1Id: string; circle2Id: string } };
          data: Record<string, unknown>;
        }) => {
          const { circle1Id, circle2Id } = where.unique_collision_pair;
          const event = collisionEvents.find(
            (e) => e.circle1Id === circle1Id && e.circle2Id === circle2Id
          );
          if (!event) {
            throw new Error('CollisionEvent not found');
          }
          Object.assign(event, data);
          return event;
        }
      )
    },
    match: {
      create: vi.fn(async ({ data }: { data: Partial<MockMatch> }) => {
        const match: MockMatch = {
          id: `match-${matches.length + 1}`,
          createdAt: new Date(),
          updatedAt: new Date(),
          primaryUserId: '',
          secondaryUserId: '',
          primaryCircleId: '',
          secondaryCircleId: '',
          type: 'match',
          worthItScore: 0.95,
          status: 'pending_accept',
          ...data
        };
        matches.push(match);
        return match;
      }),
      findFirst: vi.fn(
        async ({
          where
        }: {
          where: {
            OR?: Array<{ primaryUserId: string; secondaryUserId: string }>;
          };
        }) => {
          if (where.OR) {
            // Handle OR queries for inverse match checking
            return (
              matches.find((m) => {
                return where.OR!.some((condition) => {
                  return (
                    m.primaryUserId === condition.primaryUserId &&
                    m.secondaryUserId === condition.secondaryUserId
                  );
                });
              }) ?? null
            );
          }
          return null;
        }
      ),
      update: vi.fn(async ({ where, data }: { where: { id: string }; data: Record<string, unknown> }) => {
        const match = matches.find((m) => m.id === where.id);
        if (!match) {
          throw new Error('Match not found');
        }
        Object.assign(match, data);
        return match;
      })
    },
    chat: {
      create: vi.fn(async ({ data }: { data: Partial<MockChat> }) => {
        const chat: MockChat = {
          id: `chat-${chats.length + 1}`,
          createdAt: new Date(),
          primaryUserId: '',
          secondaryUserId: '',
          ...data
        };
        chats.push(chat);
        return chat;
      }),
      findFirst: vi.fn(
        async ({
          where
        }: {
          where: {
            OR?: Array<{ primaryUserId: string; secondaryUserId: string }>;
          };
        }) => {
          if (where.OR) {
            return (
              chats.find((c) => {
                return where.OR!.some((condition) => {
                  return (
                    c.primaryUserId === condition.primaryUserId &&
                    c.secondaryUserId === condition.secondaryUserId
                  );
                });
              }) ?? null
            );
          }
          return null;
        }
      )
    },
    circle: {
      findFirst: vi.fn(
        async ({
          where
        }: {
          where: {
            userId: string;
            status: string;
            expiresAt?: { gt: Date };
          };
        }) => {
          return (
            circles.find((c) => {
              return (
                c.userId === where.userId &&
                c.status === where.status &&
                (!where.expiresAt || c.expiresAt > where.expiresAt.gt)
              );
            }) ?? null
          );
        }
      )
    },
    $transaction: vi.fn(async (callback: (tx: unknown) => Promise<unknown>): Promise<unknown> => {
      // Simple mock: execute the callback with the prisma object itself
      // In a real transaction, this would be isolated
      return await callback(prisma);
    })
  };

  return { prisma };
});

vi.mock('../infrastructure/redis.js', () => {
  const client = {
    // Cooldown and generic hash helpers
    hgetall: vi.fn(async (key: string) => {
      return redisHashes.get(key) ?? {};
    }),
    hset: vi.fn(async (key: string, data: Record<string, unknown>) => {
      const existing = redisHashes.get(key) ?? {};
      const updated: Record<string, string> = { ...existing };
      for (const [field, value] of Object.entries(data)) {
        updated[field] = String(value);
      }
      redisHashes.set(key, updated);
      return 1;
    }),
    // Simple string storage with NX/EX lock semantics
    // Called as: set(key, value, 'EX', ttl, 'NX')
    set: vi.fn(
      async (
        key: string,
        value: string,
        mode?: string,
        _ttlSeconds?: number,
        nxFlag?: string
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
      }
    ),
    del: vi.fn(async (key: string) => {
      const hadHash = redisHashes.delete(key);
      const hadStr = redisStrings.delete(key);
      return hadHash || hadStr ? 1 : 0;
    }),
    expire: vi.fn(async (_key: string, _seconds: number) => {
      // TTL is not simulated; we just accept the call
      return 1;
    })
  };

  return {
    getRedisClient: () => client
  };
});

import { AgentMatchService, type MissionResult } from '../services/agent-match-service.js';

describe('AgentMatchService cooldowns', () => {
  let service: AgentMatchService;

  beforeEach(() => {
    missions.length = 0;
    collisionEvents.length = 0;
    matches.length = 0;
    chats.length = 0;
    circles.length = 0;
    redisHashes.clear();
    redisStrings.clear();
    service = new AgentMatchService();
  });

  it('allows matches when no cooldown is set', async () => {
    const result = await service.checkCooldown('user-1', 'user-2');
    expect(result.allowed).toBe(true);
    expect(result.reason).toBeUndefined();
  });

  it('sets and reads a notified cooldown', async () => {
    await service.setCooldown('user-1', 'user-2', 'notified');

    const key = COLLISION_CONFIG.REDIS_KEYS.cooldown('user-1', 'user-2');
    const stored = redisHashes.get(key);
    expect(stored).toBeDefined();
    expect(stored!.type).toBe('notified');

    const result = await service.checkCooldown('user-1', 'user-2');
    expect(result.allowed).toBe(false);
    expect(result.cooldownType).toBe('notified');
    expect(result.remainingMs).toBeGreaterThan(0);
  });

  it('expires cooldowns when past their expiration', async () => {
    const key = COLLISION_CONFIG.REDIS_KEYS.cooldown('user-1', 'user-2');
    // Simulate an already-expired cooldown
    redisHashes.set(key, {
      type: 'matched',
      createdAt: String(Date.now() - 10_000),
      expiresAt: String(Date.now() - 5_000)
    });

    const result = await service.checkCooldown('user-1', 'user-2');
    expect(result.allowed).toBe(true);
    expect(redisHashes.has(key)).toBe(false);
  });
});

describe('AgentMatchService mission creation', () => {
  let service: AgentMatchService;

  beforeEach(() => {
    missions.length = 0;
    collisionEvents.length = 0;
    matches.length = 0;
    chats.length = 0;
    circles.length = 0;
    redisHashes.clear();
    redisStrings.clear();
    service = new AgentMatchService();
  });

  const baseCollision = {
    circle1Id: 'circle-1',
    circle2Id: 'circle-2',
    user1Id: 'user-1',
    user2Id: 'user-2',
    distance: 100,
    timestamp: Date.now()
  };

  it('creates a mission and updates collision event when no cooldown is active', async () => {
    collisionEvents.push({
      id: 'ce-1',
      circle1Id: 'circle-1',
      circle2Id: 'circle-2',
      user1Id: 'user-1',
      user2Id: 'user-2',
      distanceMeters: 100,
      status: 'detecting'
    });

    const mission = await service.createMissionForCollision(baseCollision);
    expect(mission).not.toBeNull();
    expect(missions).toHaveLength(1);
    expect(missions[0].ownerUserId).toBe('user-1');
    expect(missions[0].visitorUserId).toBe('user-2');

    expect(collisionEvents[0].missionId).toBe(missions[0].id);
    expect(collisionEvents[0].status).toBe('mission_created');

    const lockKey = COLLISION_CONFIG.REDIS_KEYS.inFlightMission(
      baseCollision.circle1Id,
      baseCollision.circle2Id
    );
    expect(redisStrings.has(lockKey)).toBe(true);
  });

  it('skips mission creation when a cooldown is active', async () => {
    collisionEvents.push({
      id: 'ce-1',
      circle1Id: 'circle-1',
      circle2Id: 'circle-2',
      user1Id: 'user-1',
      user2Id: 'user-2',
      distanceMeters: 100,
      status: 'detecting'
    });

    await service.setCooldown('user-1', 'user-2', 'notified');

    const mission = await service.createMissionForCollision(baseCollision);
    expect(mission).toBeNull();
    expect(missions).toHaveLength(0);
  });

  it('only creates a single mission per collision due to locking', async () => {
    collisionEvents.push({
      id: 'ce-1',
      circle1Id: 'circle-1',
      circle2Id: 'circle-2',
      user1Id: 'user-1',
      user2Id: 'user-2',
      distanceMeters: 100,
      status: 'detecting'
    });

    const first = await service.createMissionForCollision(baseCollision);
    const second = await service.createMissionForCollision(baseCollision);

    expect(first).not.toBeNull();
    expect(second).toBeNull();
    expect(missions).toHaveLength(1);
  });
});

describe('AgentMatchService mission results and matches', () => {
  let service: AgentMatchService;

  beforeEach(() => {
    missions.length = 0;
    collisionEvents.length = 0;
    matches.length = 0;
    chats.length = 0;
    circles.length = 0;
    redisHashes.clear();
    redisStrings.clear();
    service = new AgentMatchService();
  });

  it('marks mission as failed and sets notified cooldown when result is unsuccessful', async () => {
    missions.push({
      id: 'mission-1',
      ownerUserId: 'user-1',
      visitorUserId: 'user-2',
      ownerCircleId: 'circle-1',
      visitorCircleId: 'circle-2',
      collisionEventId: 'ce-1',
      status: 'pending',
      attemptNumber: 1
    });

    const result: MissionResult = {
      success: false,
      matchMade: false,
      error: 'Interview failed'
    };

    const match = await service.handleMissionResult('mission-1', result);
    expect(match).toBeNull();

    expect(missions[0].status).toBe('failed');
    expect(missions[0].failureReason).toBe('Interview failed');

    const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown('user-1', 'user-2');
    const stored = redisHashes.get(cooldownKey);
    expect(stored).toBeDefined();
    expect(stored!.type).toBe('notified');
  });

  it('creates a match and sets matched cooldown when result is successful and matchMade', async () => {
    missions.push({
      id: 'mission-1',
      ownerUserId: 'user-1',
      visitorUserId: 'user-2',
      ownerCircleId: 'circle-1',
      visitorCircleId: 'circle-2',
      collisionEventId: 'ce-1',
      status: 'pending',
      attemptNumber: 1
    });

    const result: MissionResult = {
      success: true,
      matchMade: true,
      transcript: JSON.stringify({ messages: [{ role: 'interviewer', content: 'ok' }] }),
      judgeDecision: { reason: 'good fit', confidence: 0.9 }
    };

    const match = await service.handleMissionResult('mission-1', result);
    expect(match).not.toBeNull();
    expect(matches).toHaveLength(1);
    expect(matches[0].primaryUserId).toBe('user-1');
    expect(matches[0].secondaryUserId).toBe('user-2');
    expect(matches[0].status).toBe('pending_accept');

    expect(missions[0].status).toBe('completed');
    expect(missions[0].failureReason).toBeNull();
    expect(missions[0].transcript).toEqual({
      messages: [{ role: 'interviewer', content: 'ok' }]
    });

    const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown('user-1', 'user-2');
    const stored = redisHashes.get(cooldownKey);
    expect(stored).toBeDefined();
    expect(stored!.type).toBe('matched');
  });

  it('completes mission without match and sets notified cooldown when matchMade is false', async () => {
    missions.push({
      id: 'mission-1',
      ownerUserId: 'user-1',
      visitorUserId: 'user-2',
      ownerCircleId: 'circle-1',
      visitorCircleId: 'circle-2',
      collisionEventId: 'ce-1',
      status: 'pending',
      attemptNumber: 1
    });

    const result: MissionResult = {
      success: true,
      matchMade: false,
      transcript: JSON.stringify({ messages: [{ role: 'interviewer', content: 'no match' }] }),
      judgeDecision: { reason: 'not a fit', confidence: 0.7 }
    };

    const match = await service.handleMissionResult('mission-1', result);
    expect(match).toBeNull();
    expect(matches).toHaveLength(0);

    expect(missions[0].status).toBe('completed');

    const cooldownKey = COLLISION_CONFIG.REDIS_KEYS.cooldown('user-1', 'user-2');
    const stored = redisHashes.get(cooldownKey);
    expect(stored).toBeDefined();
    expect(stored!.type).toBe('notified');
  });
});

describe('AgentMatchService inverse match logic', () => {
  let service: AgentMatchService;

  beforeEach(() => {
    missions.length = 0;
    collisionEvents.length = 0;
    matches.length = 0;
    chats.length = 0;
    circles.length = 0;
    redisHashes.clear();
    redisStrings.clear();
    service = new AgentMatchService();
  });

  it('detects inverse match when user2 -> user1 match already exists', async () => {
    // Create existing match from user2 to user1
    matches.push({
      id: 'match-1',
      primaryUserId: 'user-2',
      secondaryUserId: 'user-1',
      primaryCircleId: 'circle-2',
      secondaryCircleId: 'circle-1',
      type: 'match',
      worthItScore: 0.95,
      status: 'pending_accept',
      createdAt: new Date(),
      updatedAt: new Date()
    });

    const inverseMatch = await service.checkInverseMatch('user-1', 'user-2');
    expect(inverseMatch).not.toBeNull();
    expect(inverseMatch!.id).toBe('match-1');
    expect(inverseMatch!.primaryUserId).toBe('user-2');
    expect(inverseMatch!.secondaryUserId).toBe('user-1');
  });

  it('detects inverse match when user1 -> user2 match already exists', async () => {
    // Create existing match from user1 to user2
    matches.push({
      id: 'match-1',
      primaryUserId: 'user-1',
      secondaryUserId: 'user-2',
      primaryCircleId: 'circle-1',
      secondaryCircleId: 'circle-2',
      type: 'match',
      worthItScore: 0.95,
      status: 'pending_accept',
      createdAt: new Date(),
      updatedAt: new Date()
    });

    const inverseMatch = await service.checkInverseMatch('user-2', 'user-1');
    expect(inverseMatch).not.toBeNull();
    expect(inverseMatch!.id).toBe('match-1');
  });

  it('returns null when no inverse match exists', async () => {
    const inverseMatch = await service.checkInverseMatch('user-1', 'user-2');
    expect(inverseMatch).toBeNull();
  });

  it('activates both matches and creates chat when inverse match exists', async () => {
    // Pre-existing match from user-2 to user-1
    matches.push({
      id: 'match-existing',
      primaryUserId: 'user-2',
      secondaryUserId: 'user-1',
      primaryCircleId: 'circle-2',
      secondaryCircleId: 'circle-1',
      type: 'match',
      worthItScore: 0.95,
      status: 'pending_accept',
      createdAt: new Date(),
      updatedAt: new Date()
    });

    // Mission from user-1 to user-2 completes successfully
    missions.push({
      id: 'mission-1',
      ownerUserId: 'user-1',
      visitorUserId: 'user-2',
      ownerCircleId: 'circle-1',
      visitorCircleId: 'circle-2',
      collisionEventId: 'ce-1',
      status: 'pending',
      attemptNumber: 1
    });

    const result: MissionResult = {
      success: true,
      matchMade: true,
      transcript: JSON.stringify({ messages: [] }),
      judgeDecision: { reason: 'mutual match' }
    };

    const match = await service.handleMissionResult('mission-1', result);

    // Should create a new match (user-1 -> user-2) as 'active'
    expect(match).not.toBeNull();
    expect(match!.status).toBe('active');
    expect(match!.primaryUserId).toBe('user-1');
    expect(match!.secondaryUserId).toBe('user-2');

    // Should have updated the existing match to 'active'
    expect(matches[0].status).toBe('active');

    // Should have created exactly 2 matches now (existing + new)
    expect(matches).toHaveLength(2);

    // Should have created a chat
    expect(chats).toHaveLength(1);
    expect(chats[0].primaryUserId).toBe('user-1');
    expect(chats[0].secondaryUserId).toBe('user-2');
  });

  it('does not create duplicate chat if chat already exists for mutual match', async () => {
    // Pre-existing match and chat
    matches.push({
      id: 'match-existing',
      primaryUserId: 'user-2',
      secondaryUserId: 'user-1',
      primaryCircleId: 'circle-2',
      secondaryCircleId: 'circle-1',
      type: 'match',
      worthItScore: 0.95,
      status: 'pending_accept',
      createdAt: new Date(),
      updatedAt: new Date()
    });

    chats.push({
      id: 'chat-existing',
      primaryUserId: 'user-2',
      secondaryUserId: 'user-1',
      createdAt: new Date()
    });

    missions.push({
      id: 'mission-1',
      ownerUserId: 'user-1',
      visitorUserId: 'user-2',
      ownerCircleId: 'circle-1',
      visitorCircleId: 'circle-2',
      collisionEventId: 'ce-1',
      status: 'pending',
      attemptNumber: 1
    });

    const result: MissionResult = {
      success: true,
      matchMade: true,
      transcript: JSON.stringify({ messages: [] }),
      judgeDecision: { reason: 'mutual match' }
    };

    await service.handleMissionResult('mission-1', result);

    // Should NOT create a duplicate chat
    expect(chats).toHaveLength(1);
    expect(chats[0].id).toBe('chat-existing');
  });

  it('creates pending match when no inverse match exists', async () => {
    missions.push({
      id: 'mission-1',
      ownerUserId: 'user-1',
      visitorUserId: 'user-2',
      ownerCircleId: 'circle-1',
      visitorCircleId: 'circle-2',
      collisionEventId: 'ce-1',
      status: 'pending',
      attemptNumber: 1
    });

    const result: MissionResult = {
      success: true,
      matchMade: true,
      transcript: JSON.stringify({ messages: [] }),
      judgeDecision: { reason: 'good match' }
    };

    const match = await service.handleMissionResult('mission-1', result);

    // Should create a pending match (waiting for inverse)
    expect(match).not.toBeNull();
    expect(match!.status).toBe('pending_accept');
    expect(matches).toHaveLength(1);

    // Should NOT create a chat
    expect(chats).toHaveLength(0);
  });
});

