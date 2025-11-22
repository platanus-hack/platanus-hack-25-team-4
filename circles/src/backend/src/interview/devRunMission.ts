import { BedrockInterviewAgentsRuntime } from './agentsRuntime.js';
import { InterviewFlowService } from './interviewFlowService.js';
import { BedrockInterviewJudge } from './judge.js';
import { LoggingNotificationGateway } from './notificationGateway.js';
import type { InterviewMission, UserProfile, OwnerCircle, InterviewContext } from './types.js';

const createDemoProfiles = (): {
  owner_profile: UserProfile;
  visitor_profile: UserProfile;
} => {
  const owner_profile: UserProfile = {
    id: 'owner-1',
    display_name: 'Fundador/Dev en Santiago',
    motivations_and_goals: {
      primary_goal:
        'Conectar con otros desarrolladores y fundadores en Santiago para construir side projects y compartir ideas.'
    },
    conversation_micro_preferences: {
      preferred_opener_style:
        '¡Hey! Vi que estás cerca y metido en IA/emprendimiento — me encanta conocer gente que también está construyendo cosas. ¿En qué estás ahora mismo: proyecto concreto o más exploración?'
    }
  };

  const visitor_profile: UserProfile = {
    id: 'visitor-1',
    display_name: 'Fundador de IA de visita',
    motivations_and_goals: {
      primary_goal:
        'Conocer fundadores de IA locales para compartir ideas y quizá colaborar en un MVP.'
    }
  };

  return { owner_profile, visitor_profile };
};

const createDemoCircleAndContext = (): {
  owner_circle: OwnerCircle;
  context: InterviewContext;
} => {
  const owner_circle: OwnerCircle = {
    id: 'circle-1',
    objective_text:
      'Conocer fundadores de IA en Santiago para tomar un café 1:1 y hacer brainstorming de producto.',
    radius_m: 800,
    time_window: 'tardes de esta semana'
  };

  const context: InterviewContext = {
    approximate_time_iso: new Date().toISOString(),
    approximate_distance_m: 500
  };

  return { owner_circle, context };
};

const createDemoMission = (): InterviewMission => {
  const { owner_profile, visitor_profile } = createDemoProfiles();
  const { owner_circle, context } = createDemoCircleAndContext();

  return {
    mission_id: `demo-${Date.now().toString(36)}`,
    owner_user_id: owner_profile.id,
    visitor_user_id: visitor_profile.id,
    owner_profile,
    visitor_profile,
    owner_circle,
    context
  };
};

const runDemo = async (): Promise<void> => {
  const mission = createDemoMission();

  console.log('Running demo interview mission:', mission.mission_id);

  console.log('\n=== Contexto de la misión ===');
  console.log(`Owner:   ${mission.owner_profile.display_name}`);
  console.log(`  Objetivo: ${mission.owner_profile.motivations_and_goals.primary_goal}`);
  console.log(`Visitor: ${mission.visitor_profile.display_name}`);
  console.log(`  Objetivo: ${mission.visitor_profile.motivations_and_goals.primary_goal}`);
  console.log('Circle del owner:');
  console.log(`  Objetivo: ${mission.owner_circle.objective_text}`);
  console.log(`  Ventana de tiempo: ${mission.owner_circle.time_window}`);
  console.log('Contexto aproximado:');
  console.log(
    `  Distancia entre personas: ~${mission.context.approximate_distance_m}m, hora: ${mission.context.approximate_time_iso}`
  );
  console.log('');

  const flowService = new InterviewFlowService({
    agentsRuntime: new BedrockInterviewAgentsRuntime(),
    judge: new BedrockInterviewJudge(),
    notificationGateway: new LoggingNotificationGateway(),
    config: {
      max_owner_turns: 3
    }
  });

  const result = await flowService.runMission(mission);

  console.log('\n=== Decisión del juez ===');
  console.log(JSON.stringify(result.judge_decision, null, 2));
};

void runDemo();
