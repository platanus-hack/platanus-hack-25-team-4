-- CreateTable
CREATE TABLE "CollisionEvent" (
    "id" TEXT NOT NULL,
    "user1Id" TEXT NOT NULL,
    "user2Id" TEXT NOT NULL,
    "user1CircleId" TEXT NOT NULL,
    "user2CircleId" TEXT NOT NULL,
    "distanceMeters" DOUBLE PRECISION NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'detecting',
    "stableAt" TIMESTAMP(3),
    "expiredAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "CollisionEvent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterviewMission" (
    "id" TEXT NOT NULL,
    "collisionEventId" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "InterviewMission_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "CollisionEvent_user1Id_idx" ON "CollisionEvent"("user1Id");

-- CreateIndex
CREATE INDEX "CollisionEvent_user2Id_idx" ON "CollisionEvent"("user2Id");

-- CreateIndex
CREATE INDEX "CollisionEvent_status_idx" ON "CollisionEvent"("status");

-- CreateIndex
CREATE INDEX "InterviewMission_collisionEventId_idx" ON "InterviewMission"("collisionEventId");

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_user1Id_fkey" FOREIGN KEY ("user1Id") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_user2Id_fkey" FOREIGN KEY ("user2Id") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_user1CircleId_fkey" FOREIGN KEY ("user1CircleId") REFERENCES "Circle"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_user2CircleId_fkey" FOREIGN KEY ("user2CircleId") REFERENCES "Circle"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewMission" ADD CONSTRAINT "InterviewMission_collisionEventId_fkey" FOREIGN KEY ("collisionEventId") REFERENCES "CollisionEvent"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
