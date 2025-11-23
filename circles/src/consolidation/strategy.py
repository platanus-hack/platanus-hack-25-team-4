"""
ConsolidationStrategy Protocol - Defines the interface for profile consolidation strategies.

Implementations of this protocol handle profile consolidation with injected LLM providers.
"""

import json
import logging
from typing import Any, Dict, Protocol

from pydantic import ValidationError

from ..etl.core.result import Result
from ..profile_schema import UserProfile
from .base_consolidation_strategy import BaseConsolidationStrategy
from .llm_adapter import LLMProvider, parse_json_response

logger = logging.getLogger(__name__)


class ConsolidationStrategy(Protocol):
    """
    Protocol for profile consolidation strategies.

    Implementations must handle:
    - Building consolidation prompts
    - Calling LLM for synthesis (via injected provider)
    - Parsing LLM response into UserProfile
    - Error handling and validation
    """

    async def consolidate(
        self,
        user_id: str,
        raw_data: Dict[str, Any],
        llm_provider: LLMProvider,
    ) -> Result["UserProfile", Exception]:
        """
        Consolidate user data into a complete UserProfile.

        Args:
            user_id: The user ID to consolidate for
            raw_data: Dictionary containing aggregated user data with keys:
                - resume: Processed resume data
                - photos: List of photo analyses
                - voice_notes: List of voice note transcriptions
                - chat_transcripts: List of chat transcripts
                - calendar_events: List of calendar events
                - emails: List of email data
                - social_posts: List of social media posts
                - blog_posts: List of blog posts
                - screenshots: List of screenshot analyses
                - shared_images: List of shared image analyses
            llm_provider: Injected LLM provider instance

        Returns:
            Result[UserProfile, Exception]: Success with consolidated profile or error
        """
        ...


class DefaultConsolidationStrategy(BaseConsolidationStrategy):
    """
    Default implementation of ConsolidationStrategy.

    Uses an injected LLM provider for profile synthesis.
    Inherits validation and utility methods from BaseConsolidationStrategy.
    """

    def __init__(self, user_id: str):
        """
        Initialize strategy with user context.

        Args:
            user_id: The user ID being consolidated
        """
        super().__init__(user_id)

    async def consolidate(
        self,
        user_id: str,
        raw_data: Dict[str, Any],
        llm_provider: LLMProvider,
    ) -> Result[UserProfile, Exception]:
        """
        Consolidate user data using injected LLM provider.

        Args:
            user_id: The user ID
            raw_data: Aggregated user data
            llm_provider: Injected LLM provider

        Returns:
            Result[UserProfile, Exception]: Consolidated profile or error
        """
        try:
            # Ensure user_id is set (for validation methods)
            self.user_id = user_id

            # Check if we have meaningful data to consolidate
            if not self._has_data(raw_data):
                logger.warning(f"No user data available for consolidation: {user_id}")
                return Result.error(
                    Exception("No user data available for consolidation")
                )

            # Build prompt with all user data
            prompt = self._build_consolidation_prompt(raw_data)

            # Call LLM via injected provider
            response_text = await llm_provider.call(prompt)

            # Parse JSON from response
            profile_data = parse_json_response(response_text)

            # Validate and construct profile
            return self._validate_profile(profile_data)

        except Exception as e:
            logger.error(f"Error consolidating profile for user {user_id}: {e}")
            return Result.error(e)

    def _build_consolidation_prompt(self, raw_data: Dict[str, Any]) -> str:
        """
        Build consolidation prompt for LLM.

        Args:
            raw_data: Aggregated user data

        Returns:
            Formatted prompt for LLM
        """
        data_summary = self._summarize_raw_data(raw_data)

        prompt = f"""You are an expert psychologist and data analyst specializing in user profiling.
Analyze the following user data and consolidate it into a comprehensive user profile.

USER DATA SUMMARY:
{data_summary}

DETAILED USER DATA:
{json.dumps(raw_data, indent=2, default=str)}

Based on this data, generate a JSON response with the following structure:
{{
  "bio": "<A brief 1-2 sentence personal bio or description (optional)>",
  "interests": [
    {{"title": "Interest Title", "description": "Brief description of this interest"}},
    {{"title": "Another Interest", "description": "What they do or why it matters to them"}}
  ],
  "profile_completed": <true/false - whether profile is comprehensive>,
  "personality_core": {{
    "openness": "<High/Medium/Low description>",
    "conscientiousness": "<High/Medium/Low description>",
    "extraversion": "<High/Medium/Low description>",
    "agreeableness": "<High/Medium/Low description>",
    "emotional_stability": "<High/Medium/Low description>",
    "social_match_implications": "<How personality affects social matching>"
  }},
  "social_interaction_style": {{
    "preferred_group_size": "<Solo/Pair/Small group/Large group>",
    "meeting_structure": "<Structured/Unstructured/Flexible>",
    "tone": "<Formal/Casual/Mixed>",
    "communication_style": "<Direct/Indirect/Mixed>",
    "response_latency": "<Immediate/Quick/Thoughtful>",
    "conversation_pacing": "<Fast/Moderate/Slow>",
    "comfort_zones_and_boundaries": {{
      "energy_constraints": "<Description of energy preferences>",
      "safety_preferences": "<Safety concerns or preferences>",
      "time_of_day_comfort": "<Morning/Afternoon/Evening/Flexible>",
      "pace_of_progress": "<Fast/Steady/Slow>",
      "topics_to_avoid": ["topic1", "topic2"]
    }}
  }},
  "motivations_and_goals": {{
    "primary_goal": "<User's main objective>",
    "secondary_goal": "<Secondary objectives>",
    "underlying_needs": ["need1", "need2", "need3"]
  }},
  "skills_and_identity": {{
    "skills": ["skill1", "skill2", "skill3"],
    "skill_levels": {{"skill1": "Expert", "skill2": "Intermediate"}},
    "experience": "<Years and type of experience>",
    "identity_tags": ["tag1", "tag2"]
  }},
  "lifestyle_and_rhythms": {{
    "availability": {{
      "weekday_evenings": "<Available/Limited/Unavailable>",
      "weekend_mornings": "<Available/Limited/Unavailable>"
    }},
    "weekly_rhythm": "<Weekly pattern description>",
    "preferred_locations": ["location1", "location2"],
    "mobility": {{
      "preferred_radius_km": <number>,
      "transport_modes": ["mode1", "mode2"]
    }},
    "environmental_context": {{
      "local_area_familiarity": "<High/Medium/Low>",
      "high_density_areas_exposure": "<Comfortable/Neutral/Uncomfortable>"
    }}
  }},
  "conversation_micro_preferences": {{
    "preferred_opener_style": "<Question/Statement/Story>",
    "emoji_usage": "<Frequent/Moderate/Minimal>",
    "humor_style": "<Witty/Warm/Sarcastic/None>",
    "formality_level": "<Formal/Semi-formal/Casual>",
    "preferred_medium": "<Text/Voice/Video/Flexible>",
    "default_tone": "<Tone preference>"
  }},
  "behavioral_history_model": {{
    "match_acceptance_pattern": "<Pattern of acceptance>",
    "match_decline_pattern": "<Pattern of declination>",
    "good_outcomes_pattern": "<What leads to good outcomes>",
    "response_latency_pattern": "<Typical response time>",
    "conversation_patterns": "<How conversations typically flow>"
  }},
  "agent_persona_heuristic": {{
    "voice": "<Recommended AI voice style>",
    "decision_priorities": {{"priority1": "weight", "priority2": "weight"}},
    "tone_guidance": "<How AI should communicate>",
    "risk_tolerance": "<High/Medium/Low>",
    "serendipity_openness": "<How open to unexpected matches>"
  }}
}}

IMPORTANT REQUIREMENTS:
1. Use only the data provided - infer conservatively
2. If a section lacks sufficient data, provide reasonable defaults based on available information
3. Extract 3-7 key interests from calendar, emails, social posts, and other data
4. Keep each interest title short (2-5 words) and description concise (1-2 sentences)
5. All fields are optional - include only those with sufficient data support
6. Ensure all values are strings or appropriate data types
7. Be specific and actionable in descriptions
8. Return ONLY the JSON object, no additional text"""

        return prompt
