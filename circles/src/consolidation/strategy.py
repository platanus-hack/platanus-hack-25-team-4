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
from .llm_adapter import LLMProvider, parse_json_response
from .sanitizer import sanitize_profile_data

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


class DefaultConsolidationStrategy(ConsolidationStrategy):
    """
    Default implementation of ConsolidationStrategy.

    Uses an injected LLM provider for profile synthesis.
    """

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
3. Ensure all values are strings or appropriate data types
4. Be specific and actionable in descriptions
5. Return ONLY the JSON object, no additional text"""

        return prompt


class BaseConsolidationStrategy:
    """Base implementation for consolidation strategies with common functionality."""

    def __init__(self, user_id: str):
        """Initialize with user ID."""
        self.user_id = user_id

    def _validate_profile(
        self, profile_data: Dict[str, Any]
    ) -> Result[UserProfile, Exception]:
        """
        Validate and construct UserProfile from consolidated data.

        Args:
            profile_data: Dictionary with profile fields

        Returns:
            Result[UserProfile, Exception]: Validated profile or validation error
        """
        try:
            profile_data["user_id"] = self.user_id
            profile = UserProfile(**profile_data)
            logger.debug(f"Profile validation successful for user {self.user_id}")
            return Result.ok(profile)
        except ValidationError as e:
            logger.error(f"Profile validation error for user {self.user_id}: {e}")
            return Result.error(e)
        except Exception as e:
            logger.error(
                f"Unexpected error validating profile for user {self.user_id}: {e}"
            )
            return Result.error(e)

    @staticmethod
    def _has_data(raw_data: Dict[str, Any]) -> bool:
        """Check if raw data contains any information."""
        return any(
            raw_data.get(key)
            for key in [
                "resume",
                "photos",
                "voice_notes",
                "chat_transcripts",
                "calendar_events",
                "emails",
                "social_posts",
                "blog_posts",
                "screenshots",
                "shared_images",
            ]
        )

    @staticmethod
    def _summarize_raw_data(raw_data: Dict[str, Any]) -> str:
        """Create a summary of raw data for LLM context."""
        summary_parts = []

        if raw_data.get("resume"):
            summary_parts.append(f"Resume: {raw_data['resume']}")

        if raw_data.get("photos"):
            photos = raw_data["photos"]
            count = len(photos) if isinstance(photos, list) else 1
            summary_parts.append(f"Photos: {count} photo(s) analyzed")

        if raw_data.get("voice_notes"):
            voice = raw_data["voice_notes"]
            count = len(voice) if isinstance(voice, list) else 1
            summary_parts.append(f"Voice notes: {count} note(s) transcribed")

        if raw_data.get("chat_transcripts"):
            chats = raw_data["chat_transcripts"]
            count = len(chats) if isinstance(chats, list) else 1
            summary_parts.append(f"Chat transcripts: {count} transcript(s)")

        if raw_data.get("calendar_events"):
            events = raw_data["calendar_events"]
            count = len(events) if isinstance(events, list) else 1
            summary_parts.append(f"Calendar events: {count} event(s)")

        if raw_data.get("emails"):
            emails = raw_data["emails"]
            count = len(emails) if isinstance(emails, list) else 1
            summary_parts.append(f"Emails: {count} email(s)")

        if raw_data.get("social_posts"):
            social = raw_data["social_posts"]
            count = len(social) if isinstance(social, list) else 1
            summary_parts.append(f"Social posts: {count} post(s)")

        if raw_data.get("blog_posts"):
            blogs = raw_data["blog_posts"]
            count = len(blogs) if isinstance(blogs, list) else 1
            summary_parts.append(f"Blog posts: {count} post(s)")

        if raw_data.get("screenshots"):
            screenshots = raw_data["screenshots"]
            count = len(screenshots) if isinstance(screenshots, list) else 1
            summary_parts.append(f"Screenshots: {count} screenshot(s)")

        if raw_data.get("shared_images"):
            images = raw_data["shared_images"]
            count = len(images) if isinstance(images, list) else 1
            summary_parts.append(f"Shared images: {count} image(s)")

        return "\n".join(summary_parts)
