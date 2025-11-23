export type SpeakerRole = 'owner' | 'visitor';

export type OwnerTurnGoal =
  | 'open_and_ask_one_focused_question'
  | 'clarify_objective'
  | 'clarify_availability'
  | 'decide_and_close'
  | 'notify_user';

export interface MotivationsAndGoals {
  primary_goal: string;
}

export interface ConversationMicroPreferences {
  preferred_opener_style?: string;
}

export interface UserProfile {
  id: string;
  display_name: string;
  motivations_and_goals: MotivationsAndGoals;
  conversation_micro_preferences?: ConversationMicroPreferences;
}

export interface OwnerCircle {
  id: string;
  objective_text: string;
  radius_m: number;
  time_window: string;
}

export interface InterviewContext {
  approximate_time_iso: string;
  approximate_distance_m: number;
}

export interface TranscriptMessage {
  speaker: SpeakerRole;
  message: string;
}

export interface AgentTurnMetadata {
  intent_tag?:
    | 'clarify_goal'
    | 'clarify_time'
    | 'clarify_place'
    | 'propose_meet'
    | 'decline'
    | 'small_talk';
  stop_suggested?: boolean;
}

export interface AgentTurnOutput extends AgentTurnMetadata {
  as_user_message: string;
}

export interface OwnerTurnInput {
  owner_profile: UserProfile;
  visitor_profile: UserProfile;
  owner_circle: OwnerCircle;
  context: InterviewContext;
  conversation_so_far: TranscriptMessage[];
  turn_goal: OwnerTurnGoal;
}

export interface VisitorTurnInput {
  visitor_profile: UserProfile;
  owner_profile: UserProfile;
  context: InterviewContext;
  conversation_so_far: TranscriptMessage[];
}

export interface JudgeInput {
  owner_objective: string;
  transcript: TranscriptMessage[];
}

export interface JudgeDecision {
  should_notify: boolean;
  notification_text?: string;
  /**
   * Short natural-language summary of the agent-to-agent conversation.
   * Should start with: "Summary of agent interaction: ..."
   */
  summary_text?: string;
}

export interface InterviewMission {
  mission_id: string;
  owner_user_id: string;
  visitor_user_id: string;
  owner_profile: UserProfile;
  visitor_profile: UserProfile;
  owner_circle: OwnerCircle;
  context: InterviewContext;
}

export interface InterviewMissionResult {
  mission_id: string;
  transcript: TranscriptMessage[];
  judge_decision: JudgeDecision;
}

export interface InterviewFlowConfig {
  max_owner_turns: number;
}

export interface NotificationPayload {
  mission_id: string;
  owner_user_id: string;
  visitor_user_id: string;
  notification_text: string;
}
