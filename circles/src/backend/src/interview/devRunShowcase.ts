import { writeFile } from 'fs/promises';

import { BedrockInterviewAgentsRuntime } from './agentsRuntime.js';
import { InterviewFlowService } from './interviewFlowService.js';
import { BedrockInterviewJudge } from './judge.js';
import { MOCK_USER_PROFILES } from './mockProfiles.js';
import { LoggingNotificationGateway } from './notificationGateway.js';
import type {
  InterviewContext,
  InterviewMission,
  InterviewMissionResult,
  OwnerCircle,
  TranscriptMessage,
  UserProfile
} from './types.js';

interface ShowcaseScenario {
  scenario_id: string;
  description: string;
  owner_profile_id: string;
  visitor_profile_id: string;
  owner_circle: OwnerCircle;
  context: InterviewContext;
}

interface ShowcaseMissionResult {
  scenario_id: string;
  description: string;
  mission_id: string;
  owner_profile: UserProfile;
  visitor_profile: UserProfile;
  owner_circle: OwnerCircle;
  context: InterviewContext;
  transcript: TranscriptMessage[];
  judge_decision: InterviewMissionResult['judge_decision'];
}

const findProfile = (id: string): UserProfile => {
  const profile = MOCK_USER_PROFILES.find((p) => p.id === id);
  if (!profile) {
    throw new Error(`Profile with id "${id}" not found in MOCK_USER_PROFILES.`);
  }
  return profile;
};

const createShowcaseScenarios = (): ShowcaseScenario[] => {
  const nowIso = new Date().toISOString();

  const baseContext = (distanceM: number): InterviewContext => ({
    approximate_time_iso: nowIso,
    approximate_distance_m: distanceM
  });

  const scenarios: ShowcaseScenario[] = [
    {
      scenario_id: 'job_frontend_hiring',
      description:
        'Desarrolladora front-end buscando trabajo se cruza con tech lead que está contratando para startup B2B.',
      owner_profile_id: 'user-camila-dev-jobseeker',
      visitor_profile_id: 'user-francisco-tech-lead-hiring',
      owner_circle: {
        id: 'circle-job-1',
        objective_text:
          'Encontrar pega como dev front-end en una startup B2B en Santiago donde pueda aprender y aportar rápido.',
        radius_m: 800,
        time_window: 'tardes de esta semana'
      },
      context: baseContext(600)
    },
    {
      scenario_id: 'job_pm_recruiter',
      description:
        'Product manager en transición que quiere entender oportunidades se cruza con recruiter tech que busca perfiles.',
      owner_profile_id: 'user-valentina-product-manager-jobseeker',
      visitor_profile_id: 'user-jorge-hr-recruiter',
      owner_circle: {
        id: 'circle-job-2',
        objective_text:
          'Conectar con gente que conozca oportunidades de PM early stage en Santiago para entender fit y procesos.',
        radius_m: 1000,
        time_window: 'tardes y noches de esta semana'
      },
      context: baseContext(750)
    },
    {
      scenario_id: 'gaming_fps_partners',
      description:
        'Jugador de FPS buscando partners para rankear se cruza con fan de juegos de pelea que también juega online.',
      owner_profile_id: 'user-nico-gamer-fps',
      visitor_profile_id: 'user-rodrigo-gamer-fighting',
      owner_circle: {
        id: 'circle-games-1',
        objective_text:
          'Encontrar dúo/trío buena onda para rankear Valorant/CS en las noches sin tanto tilt.',
        radius_m: 5000,
        time_window: 'noches de esta semana'
      },
      context: baseContext(1200)
    },
    {
      scenario_id: 'books_reading_match',
      description:
        'Organizador de club de lectura en Ñuñoa se cruza con persona interesada en intercambio de libros físicos.',
      owner_profile_id: 'user-alejandro-bookclub',
      visitor_profile_id: 'user-constanza-book-exchange',
      owner_circle: {
        id: 'circle-books-1',
        objective_text:
          'Armar club de lectura piola en Ñuñoa para leer novelas contemporáneas y no-ficción una vez por semana.',
        radius_m: 1000,
        time_window: 'fines de semana'
      },
      context: baseContext(400)
    },
    {
      scenario_id: 'sports_padel_match',
      description:
        'Jugador de pádel buscando partner intermedio/avanzado se cruza con persona que juega tenis y le interesan deportes de raqueta.',
      owner_profile_id: 'user-diego-padel-player',
      visitor_profile_id: 'user-sofia-tennis-player',
      owner_circle: {
        id: 'circle-sports-1',
        objective_text:
          'Encontrar partner fijo de pádel nivel intermedio/avanzado para jugar 2–3 veces por semana en Las Condes/Vitacura.',
        radius_m: 3000,
        time_window: 'tardes después de la pega'
      },
      context: baseContext(1500)
    },
    {
      scenario_id: 'sports_chess_vs_football_no_match',
      description:
        'Ajedrecista tranquilo se cruza con persona que quiere equipo de fútbol mixto con energía alta — posible no match.',
      owner_profile_id: 'user-pedro-chess-player',
      visitor_profile_id: 'user-loreto-football',
      owner_circle: {
        id: 'circle-sports-2',
        objective_text:
          'Encontrar personas que disfruten partidas largas de ajedrez en vivo o en línea, con análisis calmado después.',
        radius_m: 800,
        time_window: 'fines de semana en la tarde'
      },
      context: baseContext(700)
    },
    {
      scenario_id: 'afteroffice_match',
      description:
        'Persona de tech que busca after office tranqui con gente de startups se cruza con fan de bares y cocteles tranquilos.',
      owner_profile_id: 'user-catalina-afteroffice',
      visitor_profile_id: 'user-tomas-cocktail-bars',
      owner_circle: {
        id: 'circle-night-1',
        objective_text:
          'Armar grupo pequeño para after office en Lastarria/Providencia, conversar de proyectos y vida en Santiago.',
        radius_m: 2000,
        time_window: 'tardes y noches de la semana'
      },
      context: baseContext(900)
    },
    {
      scenario_id: 'nightlife_vs_quiet_reader_no_match',
      description:
        'Lectora tranquila que prefiere actividades calmadas se cruza con fan de bares/karaoke/after — probable que no valga la pena notificar.',
      owner_profile_id: 'user-fernanda-quiet-reader',
      visitor_profile_id: 'user-matias-nightlife',
      owner_circle: {
        id: 'circle-books-2',
        objective_text:
          'Conocer gente piola para compartir recomendaciones de libros y quizá juntarse a leer/tomar café, sin carrete intenso.',
        radius_m: 1500,
        time_window: 'fines de semana en la tarde'
      },
      context: baseContext(600)
    },
    {
      scenario_id: 'career_switch_advice',
      description:
        'Persona cambiando de rubro hacia tech quiere consejos y se cruza con alguien fuerte en after office de tech/startups.',
      owner_profile_id: 'user-ricardo-career-switch',
      visitor_profile_id: 'user-catalina-afteroffice',
      owner_circle: {
        id: 'circle-career-1',
        objective_text:
          'Hablar con gente que ya hizo cambio de carrera hacia tech o producto en Chile para entender caminos reales y errores comunes.',
        radius_m: 2000,
        time_window: 'tardes de esta semana'
      },
      context: baseContext(800)
    },
    {
      scenario_id: 'running_morning_only',
      description:
        'Corredor mañanero busca partners para trotar temprano; según el perfil visitante podría que no se alinee tanto.',
      owner_profile_id: 'user-alvaro-running',
      visitor_profile_id: 'user-isa-minimal-social',
      owner_circle: {
        id: 'circle-sports-3',
        objective_text:
          'Conectar con personas que quieran salir a trotar temprano por el Parque Bustamante o el río Mapocho 3–4 veces a la semana.',
        radius_m: 2500,
        time_window: 'mañanas de lunes a viernes'
      },
      context: baseContext(1000)
    }
  ];

  return scenarios;
};

const buildMissionFromScenario = (scenario: ShowcaseScenario, missionIndex: number): InterviewMission => {
  const owner_profile = findProfile(scenario.owner_profile_id);
  const visitor_profile = findProfile(scenario.visitor_profile_id);

  const missionId = `showcase-${scenario.scenario_id}-${missionIndex}-${Date.now().toString(36)}`;

  return {
    mission_id: missionId,
    owner_user_id: owner_profile.id,
    visitor_user_id: visitor_profile.id,
    owner_profile,
    visitor_profile,
    owner_circle: scenario.owner_circle,
    context: scenario.context
  };
};

const runShowcase = async (): Promise<void> => {
  const scenarios = createShowcaseScenarios();

  const flowService = new InterviewFlowService({
    agentsRuntime: new BedrockInterviewAgentsRuntime(),
    judge: new BedrockInterviewJudge(),
    notificationGateway: new LoggingNotificationGateway(),
    config: {
      max_owner_turns: 3
    }
  });

  console.log(`Running ${scenarios.length} showcase interview missions in parallel...\n`);

  const missionsResults: ShowcaseMissionResult[] = await Promise.all(
    scenarios.map(async (scenario, index) => {
      const mission = buildMissionFromScenario(scenario, index);

      const result: InterviewMissionResult = await flowService.runMission(mission);

      return {
        scenario_id: scenario.scenario_id,
        description: scenario.description,
        mission_id: result.mission_id,
        owner_profile: mission.owner_profile,
        visitor_profile: mission.visitor_profile,
        owner_circle: mission.owner_circle,
        context: mission.context,
        transcript: result.transcript,
        judge_decision: result.judge_decision
      };
    })
  );

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const outputPath = `interview_showcase_results_${timestamp}.json`;

  await writeFile(outputPath, JSON.stringify(missionsResults, null, 2), 'utf-8');

  console.log(`\nShowcase complete. Results written to: ${outputPath}`);
};

void runShowcase();

