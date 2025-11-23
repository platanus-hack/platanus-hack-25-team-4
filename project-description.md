# Circles – AI-Powered Location-Based Social Network

## Executive Summary

**Circles** is a location-based social network powered by AI agents that connects people around shared objectives and real-world intentions. Users create "Circles" – intention bubbles represented by personalized AI agent personas – that collide in the real world to facilitate authentic, high-quality connections.

## The Problem

Traditional location-based social apps suffer from:

- **Passive Discovery**: Users endlessly browse similar profiles without understanding intent or compatibility
- **Low Match Quality**: No real assessment of whether two people will actually enjoy connecting
- **Compromised Privacy**: Too much personal data exposed during discovery
- **Decision Fatigue**: Overwhelming number of options without quality criteria

## The Solution

Circles uses **AI agent personas** built from existing digital traces (social media, chats, events) to:

1. **Create Circles**: Specify objectives (e.g., "Play tennis this evening in Palermo"), radius, and duration
2. **Detect Collisions**: When circles overlap geographically, agents evaluate compatibility
3. **Simulate Interactions**: Agents conduct brief simulated conversations to assess if connection is truly "worth it"
4. **Present Matches**: Strong alignments open direct chats with agent-generated explanations

### Key Features

- **Personalized AI Agents**: Each user has an agent that learns their interests, communication style, and boundaries
- **Semantic Matching**: Uses embeddings to intelligently align objectives and interests
- **Multiple Circles**: Users can maintain multiple active circles simultaneously for different purposes
- **Privacy-Preserving**: Agents explain matches without exposing sensitive personal data
- **Agent Simulations**: Automated evaluations of connection potential before contacting users

## Technology Stack

### Backend

- **Framework**: Express.js (Node.js + TypeScript)
- **Database**: PostgreSQL with PostGIS extension
- **ORM**: Prisma (type-safe, automatic migrations)
- **Validation**: Zod (runtime validation with TypeScript type inference)
- **Authentication**: Passport.js + JWT + bcrypt
- **Message Queue**: BullMQ (for async agent processing)
- **Cache**: Redis (geospatial indexes and session caching)

### Mobile Frontend

- **Framework**: Flutter (Dart)
- **Features**: Background location, push notifications, real-time chat with WebSockets

### AI Features

- **LLM Models**: AWS Bedrock for agent simulations
- **Embeddings**: Semantic vector processing of objectives and interests
- **Profile Building**: Multi-source data consolidation and analysis

## Core User Flow

1. **Onboarding**: User registers, optionally connects data sources (social media), completes questionnaire
2. **Agent Creation**: Backend builds an AI persona from collected data
3. **Create Circle**: User specifies objective, radius, duration
4. **Collision Detection**: System identifies geographically overlapping circles
5. **Compatibility Evaluation**:
   - Semantic matching: Compare objectives and interests
   - Agent simulation: Agents converse to evaluate "worth it score"
6. **Match Presentation**: Strong matches open direct chat; soft matches request consent
7. **Chat**: 1:1 communication with AI-generated suggestions

## Success Metrics

- Match Quality (measured by engagement and user feedback)
- Privacy: Zero exposure of non-consented sensitive data
- Adoption: Active users creating multiple circles
- Safety: Detection and prevention of malicious behavior

## Key Differentiators

1. **Real Agents**: Not just algorithmic filtering – agents simulate actual conversations
2. **Privacy by Design**: Agents explain connections without exposing sensitive data
3. **Real Intention**: Circles are based on concrete objectives, not just interests
4. **Quality Over Quantity**: Few high-quality matches instead of many superficial ones

## Why Circles Matters

- **Consumer AI Track**: Demonstrates practical application of AI agents to solve real social friction
- **Innovation**: Uses multi-agent simulations for authentic human connection discovery
- **Technical Depth**: Combines geospatial indexing, semantic embeddings, and LLM agent orchestration
- **Privacy-First**: Shows how AI can enhance experiences while protecting user data

---

*Circles is the result of a 36-hour hackathon. We're building the future of meaningful human connection.*
