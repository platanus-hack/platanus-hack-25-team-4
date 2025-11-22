import { MockInterviewAgentsRuntime } from './agentsRuntime.js';
import { InterviewFlowService } from './interviewFlowService.js';
import { MockInterviewJudge } from './judge.js';
import { LoggingNotificationGateway } from './notificationGateway.js';
import type { InterviewMission, UserProfile, OwnerCircle, InterviewContext } from './types.js';

const createDemoProfiles = (): {
  owner_profile: UserProfile;
  visitor_profile: UserProfile;
} => {
  const owner_profile: UserProfile = {
    id: 'owner-1',
    display_name: 'Founder/Dev in Santiago',
    motivations_and_goals: {
      primary_goal: 'Connect with fellow developers/entrepreneurs in Santiago to build side-projects and share ideas.'
    },
    conversation_micro_preferences: {
      preferred_opener_style:
        'Hey! Noticed you are nearby and into tech/side projects — want to see if we might build or brainstorm something together this week?'
    }
  };

  const visitor_profile: UserProfile = {
    id: 'visitor-1',
    display_name: 'AI Founder visiting',
    motivations_and_goals: {
      primary_goal: 'Meet local AI founders to share ideas and maybe collaborate on an MVP.'
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
    objective_text: 'Meet AI founders in Santiago for 1:1 coffee and product brainstorms.',
    radius_m: 800,
    time_window: 'this week evenings'
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

  const flowService = new InterviewFlowService({
    agentsRuntime: new MockInterviewAgentsRuntime(),
    judge: new MockInterviewJudge(),
    notificationGateway: new LoggingNotificationGateway(),
    config: {
      max_owner_turns: 3
    }
  });

  console.log('Running demo interview mission:', mission.mission_id);

  const result = await flowService.runMission(mission);

  console.log('\n--- Transcript ---');
  for (const turn of result.transcript) {
    console.log(`[${turn.speaker.toUpperCase()}] ${turn.message}`);
  }

  console.log('\n--- Judge Decision ---');
  console.log(JSON.stringify(result.judge_decision, null, 2));
};

void runDemo();
