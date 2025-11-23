/*
  Warnings:

  - You are about to drop the column `expiredAt` on the `CollisionEvent` table. All the data in the column will be lost.
  - You are about to drop the column `stableAt` on the `CollisionEvent` table. All the data in the column will be lost.
  - You are about to drop the column `user1CircleId` on the `CollisionEvent` table. All the data in the column will be lost.
  - You are about to drop the column `user2CircleId` on the `CollisionEvent` table. All the data in the column will be lost.
  - You are about to drop the column `updatedAt` on the `InterviewMission` table. All the data in the column will be lost.
  - A unique constraint covering the columns `[missionId]` on the table `CollisionEvent` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[matchId]` on the table `CollisionEvent` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[circle1Id,circle2Id]` on the table `CollisionEvent` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[collisionEventId]` on the table `InterviewMission` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[collisionEventId]` on the table `Match` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `circle1Id` to the `CollisionEvent` table without a default value. This is not possible if the table is not empty.
  - Added the required column `circle2Id` to the `CollisionEvent` table without a default value. This is not possible if the table is not empty.
  - Added the required column `firstSeenAt` to the `CollisionEvent` table without a default value. This is not possible if the table is not empty.
  - Changed the type of `status` on the `CollisionEvent` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.
  - Added the required column `ownerCircleId` to the `InterviewMission` table without a default value. This is not possible if the table is not empty.
  - Added the required column `ownerUserId` to the `InterviewMission` table without a default value. This is not possible if the table is not empty.
  - Added the required column `visitorCircleId` to the `InterviewMission` table without a default value. This is not possible if the table is not empty.
  - Added the required column `visitorUserId` to the `InterviewMission` table without a default value. This is not possible if the table is not empty.
  - Changed the type of `status` on the `InterviewMission` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.

*/
-- CreateEnum
CREATE TYPE "CollisionStatus" AS ENUM ('detecting', 'stable', 'mission_created', 'matched', 'cooldown', 'expired');

-- CreateEnum
CREATE TYPE "MissionStatus" AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');

-- DropForeignKey
ALTER TABLE "CollisionEvent" DROP CONSTRAINT "CollisionEvent_user1CircleId_fkey";

-- DropForeignKey
ALTER TABLE "CollisionEvent" DROP CONSTRAINT "CollisionEvent_user1Id_fkey";

-- DropForeignKey
ALTER TABLE "CollisionEvent" DROP CONSTRAINT "CollisionEvent_user2CircleId_fkey";

-- DropForeignKey
ALTER TABLE "CollisionEvent" DROP CONSTRAINT "CollisionEvent_user2Id_fkey";

-- DropIndex
DROP INDEX "CollisionEvent_user1Id_idx";

-- DropIndex
DROP INDEX "CollisionEvent_user2Id_idx";

-- DropIndex
DROP INDEX "InterviewMission_collisionEventId_idx";

-- AlterTable
ALTER TABLE "CollisionEvent" DROP COLUMN "expiredAt",
DROP COLUMN "stableAt",
DROP COLUMN "user1CircleId",
DROP COLUMN "user2CircleId",
ADD COLUMN     "circle1Id" TEXT NOT NULL,
ADD COLUMN     "circle2Id" TEXT NOT NULL,
ADD COLUMN     "detectedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN     "firstSeenAt" TIMESTAMP(3) NOT NULL,
ADD COLUMN     "matchId" TEXT,
ADD COLUMN     "missionId" TEXT,
ADD COLUMN     "processedAt" TIMESTAMP(3),
ADD COLUMN     "processingError" TEXT,
DROP COLUMN "status",
ADD COLUMN     "status" "CollisionStatus" NOT NULL;

-- AlterTable
ALTER TABLE "InterviewMission" DROP COLUMN "updatedAt",
ADD COLUMN     "attemptNumber" INTEGER NOT NULL DEFAULT 1,
ADD COLUMN     "completedAt" TIMESTAMP(3),
ADD COLUMN     "failureReason" TEXT,
ADD COLUMN     "judgeDecision" JSONB,
ADD COLUMN     "ownerCircleId" TEXT NOT NULL,
ADD COLUMN     "ownerUserId" TEXT NOT NULL,
ADD COLUMN     "startedAt" TIMESTAMP(3),
ADD COLUMN     "transcript" JSONB,
ADD COLUMN     "visitorCircleId" TEXT NOT NULL,
ADD COLUMN     "visitorUserId" TEXT NOT NULL,
DROP COLUMN "status",
ADD COLUMN     "status" "MissionStatus" NOT NULL;

-- AlterTable
ALTER TABLE "Match" ADD COLUMN     "collisionEventId" TEXT;

-- CreateIndex
CREATE INDEX "idx_circle_status" ON "Circle"("status", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "CollisionEvent_missionId_key" ON "CollisionEvent"("missionId");

-- CreateIndex
CREATE INDEX "idx_collision_stability" ON "CollisionEvent"("status", "firstSeenAt");

-- CreateIndex
CREATE INDEX "idx_collision_users" ON "CollisionEvent"("user1Id", "user2Id");

-- CreateIndex
CREATE INDEX "idx_collision_status" ON "CollisionEvent"("status");

-- CreateIndex
CREATE INDEX "idx_collision_created" ON "CollisionEvent"("createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "CollisionEvent_matchId_key" ON "CollisionEvent"("matchId");

-- CreateIndex
CREATE UNIQUE INDEX "CollisionEvent_circle1Id_circle2Id_key" ON "CollisionEvent"("circle1Id", "circle2Id");

-- CreateIndex
CREATE UNIQUE INDEX "InterviewMission_collisionEventId_key" ON "InterviewMission"("collisionEventId");

-- CreateIndex
CREATE INDEX "idx_mission_status" ON "InterviewMission"("status", "createdAt");

-- CreateIndex
CREATE INDEX "idx_mission_users" ON "InterviewMission"("ownerUserId", "visitorUserId");

-- CreateIndex
CREATE INDEX "idx_mission_current" ON "InterviewMission"("status");

-- CreateIndex
CREATE UNIQUE INDEX "Match_collisionEventId_key" ON "Match"("collisionEventId");

-- AddForeignKey
ALTER TABLE "Match" ADD CONSTRAINT "Match_collisionEventId_fkey" FOREIGN KEY ("collisionEventId") REFERENCES "CollisionEvent"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_circle1Id_fkey" FOREIGN KEY ("circle1Id") REFERENCES "Circle"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_circle2Id_fkey" FOREIGN KEY ("circle2Id") REFERENCES "Circle"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_user1Id_fkey" FOREIGN KEY ("user1Id") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollisionEvent" ADD CONSTRAINT "CollisionEvent_user2Id_fkey" FOREIGN KEY ("user2Id") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewMission" ADD CONSTRAINT "InterviewMission_ownerUserId_fkey" FOREIGN KEY ("ownerUserId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewMission" ADD CONSTRAINT "InterviewMission_visitorUserId_fkey" FOREIGN KEY ("visitorUserId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewMission" ADD CONSTRAINT "InterviewMission_ownerCircleId_fkey" FOREIGN KEY ("ownerCircleId") REFERENCES "Circle"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewMission" ADD CONSTRAINT "InterviewMission_visitorCircleId_fkey" FOREIGN KEY ("visitorCircleId") REFERENCES "Circle"("id") ON DELETE CASCADE ON UPDATE CASCADE;
