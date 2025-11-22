"""
SQLModel database schemas for user profiles.

This module defines the data models for storing user profile information
including personality traits, social preferences, skills, and lifestyle patterns.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from pydantic import Field as PydanticField
from sqlmodel import JSON, Field, SQLModel

# ============================================================================
# Pydantic models for JSON fields (flexible data structures)
# ============================================================================


class PersonalityCore(BaseModel):
    """Core personality traits based on Big Five model."""

    openness: str
    conscientiousness: str
    extraversion: str
    agreeableness: str
    emotional_stability: str
    social_match_implications: str


class ComfortZonesAndBoundaries(BaseModel):
    """User's comfort zones and interaction boundaries."""

    energy_constraints: str
    safety_preferences: str
    time_of_day_comfort: str
    pace_of_progress: str
    topics_to_avoid: List[str]


class SocialInteractionStyle(BaseModel):
    """User's preferred social interaction patterns."""

    preferred_group_size: str
    meeting_structure: str
    tone: str
    communication_style: str
    response_latency: str
    conversation_pacing: str
    comfort_zones_and_boundaries: ComfortZonesAndBoundaries


class MotivationsAndGoals(BaseModel):
    """User's primary and secondary goals."""

    primary_goal: str
    secondary_goal: str
    underlying_needs: List[str]


class SkillLevel(BaseModel):
    """Skill proficiency level."""

    skill_name: str
    level: str


class SkillsAndIdentity(BaseModel):
    """User's skills and identity tags."""

    skills: List[str]
    skill_levels: dict  # skill_name -> proficiency level
    experience: str
    identity_tags: List[str]


class Availability(BaseModel):
    """User's availability schedule."""

    weekday_evenings: str
    weekend_mornings: str


class Mobility(BaseModel):
    """User's mobility and transportation preferences."""

    preferred_radius_km: int
    transport_modes: List[str]


class EnvironmentalContext(BaseModel):
    """User's local area context."""

    local_area_familiarity: str
    high_density_areas_exposure: str


class LifestyleAndRhythms(BaseModel):
    """User's lifestyle patterns and daily rhythms."""

    availability: Availability
    weekly_rhythm: str
    mobility: Mobility
    preferred_locations: List[str]
    environmental_context: EnvironmentalContext


class ConversationMicroPreferences(BaseModel):
    """User's micro-level conversation preferences."""

    preferred_opener_style: str
    emoji_usage: str
    humor_style: str
    formality_level: str
    preferred_medium: str
    default_tone: str


class BehaviouralHistoryModel(BaseModel):
    """Patterns from user's historical behavior."""

    match_acceptance_pattern: str
    match_decline_pattern: str
    good_outcomes_pattern: str
    response_latency_pattern: str
    conversation_patterns: str


class AgentPersonaHeuristic(BaseModel):
    """Decision-making heuristics for the matching agent."""

    voice: str
    decision_priorities: dict  # numeric key -> priority description
    tone_guidance: str
    risk_tolerance: str
    serendipity_openness: str


class Interest(BaseModel):
    """User interest with title and description."""

    title: str
    description: str


class InterestsList(BaseModel):
    """List of user interests."""

    interests: List[Interest]


# ============================================================================
# SQLModel database models
# ============================================================================


class UserProfile(SQLModel, table=True):
    """Main user profile database model.

    This model stores comprehensive user profile information including
    personality, social preferences, skills, and lifestyle patterns.
    """

    # Primary key and metadata
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Core personality traits
    personality_core: Optional[PersonalityCore] = Field(default=None, sa_type=JSON)

    # Social interaction style
    social_interaction_style: Optional[SocialInteractionStyle] = Field(
        default=None, sa_type=JSON
    )

    # Motivations and goals
    motivations_and_goals: Optional[MotivationsAndGoals] = Field(
        default=None, sa_type=JSON
    )

    # Skills and identity
    skills_and_identity: Optional[SkillsAndIdentity] = Field(default=None, sa_type=JSON)

    # Lifestyle and rhythms
    lifestyle_and_rhythms: Optional[LifestyleAndRhythms] = Field(
        default=None, sa_type=JSON
    )

    # Conversation preferences
    conversation_micro_preferences: Optional[ConversationMicroPreferences] = Field(
        default=None, sa_type=JSON
    )

    # Behavioural history
    behavioural_history_model: Optional[BehaviouralHistoryModel] = Field(
        default=None, sa_type=JSON
    )

    # Agent heuristics
    agent_persona_heuristic: Optional[AgentPersonaHeuristic] = Field(
        default=None, sa_type=JSON
    )

    # User interests and profile completion
    bio: Optional[str] = Field(default=None)
    interests: Optional[InterestsList] = Field(default=None, sa_type=JSON)
    profile_completed: Optional[bool] = Field(default=False)

    # Metadata
    is_active: bool = Field(default=True, index=True)
    last_matched: Optional[datetime] = Field(default=None)


class UserProfileRead(SQLModel):
    """Schema for reading user profiles (response model)."""

    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    personality_core: Optional[PersonalityCore] = None
    social_interaction_style: Optional[SocialInteractionStyle] = None
    motivations_and_goals: Optional[MotivationsAndGoals] = None
    skills_and_identity: Optional[SkillsAndIdentity] = None
    lifestyle_and_rhythms: Optional[LifestyleAndRhythms] = None
    conversation_micro_preferences: Optional[ConversationMicroPreferences] = None
    behavioural_history_model: Optional[BehaviouralHistoryModel] = None
    agent_persona_heuristic: Optional[AgentPersonaHeuristic] = None
    bio: Optional[str] = None
    interests: Optional[InterestsList] = None
    profile_completed: Optional[bool] = None
    is_active: bool
    last_matched: Optional[datetime] = None


class UserProfileCreate(SQLModel):
    """Schema for creating user profiles (request model)."""

    user_id: str
    personality_core: Optional[PersonalityCore] = None
    social_interaction_style: Optional[SocialInteractionStyle] = None
    motivations_and_goals: Optional[MotivationsAndGoals] = None
    skills_and_identity: Optional[SkillsAndIdentity] = None
    lifestyle_and_rhythms: Optional[LifestyleAndRhythms] = None
    conversation_micro_preferences: Optional[ConversationMicroPreferences] = None
    behavioural_history_model: Optional[BehaviouralHistoryModel] = None
    agent_persona_heuristic: Optional[AgentPersonaHeuristic] = None
    bio: Optional[str] = None
    interests: Optional[InterestsList] = None
    profile_completed: Optional[bool] = None
