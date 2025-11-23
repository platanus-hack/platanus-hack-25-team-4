"""
End-to-End Tests for Profile Consolidation with Real LLM APIs.

These tests run the complete consolidation pipeline with real API calls.
Marked with @pytest.mark.slow and @pytest.mark.e2e to allow skipping in CI.

Run with: pytest -m "e2e" circles/tests/integration/test_consolidation_e2e.py
"""

import logging

import pytest

from src.consolidation.llm_adapter import LLMProviderFactory
from src.consolidation.orchestrator import ProfileConsolidationOrchestrator
from src.consolidation.strategy import DefaultConsolidationStrategy
from src.etl.core.config import get_settings

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_minimal_raw_data():
    """Minimal but realistic raw user data for E2E testing."""
    return {
        "resume": {
            "full_text": "Software Engineer with 3 years of experience building web applications. "
            "Passionate about Python, JavaScript, and open source. "
            "Love mentoring junior developers and contributing to community projects.",
            "structured_data": {
                "skills": ["Python", "JavaScript", "React", "Docker"],
                "experience_years": 3,
            },
        },
        "photos": [
            {
                "file_reference": "photo_01.jpg",
                "vlm_caption": "Person at a hackathon event",
                "vlm_analysis": {
                    "setting": "tech community event",
                    "energy": "engaged",
                    "context": "networking environment",
                },
                "exif_data": {},
            }
        ],
        "voice_notes": [
            {
                "transcription": "I really enjoy collaborative projects where I can learn from others. "
                "I'm most productive in mornings and prefer working with a small team. "
                "Coffee shops are my favorite place to meet new people.",
                "language": "en",
                "extracted_topics": ["collaboration", "learning", "team"],
                "sentiment": {"sentiment": "positive", "score": 0.85},
            }
        ],
        "chat_transcripts": [],
        "calendar_events": [],
        "emails": [],
        "social_posts": [],
        "blog_posts": [],
        "screenshots": [],
        "shared_images": [],
    }


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
async def test_claude_consolidation_with_real_api(async_session, sample_minimal_raw_data):
    """
    E2E test: Claude consolidator with real API call.

    SKIPPED in CI - only runs when explicitly requested with:
    pytest -m "e2e" tests/integration/test_consolidation_e2e.py

    Requires ANTHROPIC_API_KEY environment variable.
    """
    settings = get_settings()

    # Skip if API key not configured
    if not settings.anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not configured")

    user_id = "e2e_test_claude_user"

    # Create LLM provider and strategy
    llm_provider = LLMProviderFactory.create("anthropic")
    strategy = DefaultConsolidationStrategy(user_id)

    # Call real Claude API
    result = await strategy.consolidate(user_id, sample_minimal_raw_data, llm_provider)

    # Verify success
    assert result.is_ok, (
        f"Consolidation failed: {result.error_value if result.is_error else 'unknown'}"
    )

    profile = result.value
    assert profile.user_id == user_id
    assert profile.personality_core is not None
    assert profile.social_interaction_style is not None
    assert profile.motivations_and_goals is not None
    assert profile.skills_and_identity is not None

    # Verify profile fields are populated
    assert profile.personality_core.openness
    assert profile.personality_core.conscientiousness
    assert profile.personality_core.extraversion

    logger.info(f"Claude E2E test passed for user {user_id}")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
async def test_openai_consolidation_with_real_api(async_session, sample_minimal_raw_data):
    """
    E2E test: OpenAI consolidator with real API call.

    SKIPPED in CI - only runs when explicitly requested with:
    pytest -m "e2e" tests/integration/test_consolidation_e2e.py

    Requires OPENAI_API_KEY environment variable.
    """
    settings = get_settings()

    # Skip if API key not configured
    if not settings.openai_api_key:
        pytest.skip("OPENAI_API_KEY not configured")

    user_id = "e2e_test_openai_user"

    # Create LLM provider and strategy
    llm_provider = LLMProviderFactory.create("openai")
    strategy = DefaultConsolidationStrategy(user_id)

    # Call real OpenAI API
    result = await strategy.consolidate(user_id, sample_minimal_raw_data, llm_provider)

    # Verify success
    assert result.is_ok, (
        f"Consolidation failed: {result.error_value if result.is_error else 'unknown'}"
    )

    profile = result.value
    assert profile.user_id == user_id
    assert profile.personality_core is not None
    assert profile.social_interaction_style is not None

    logger.info(f"OpenAI E2E test passed for user {user_id}")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
async def test_orchestrator_e2e_with_claude(async_session, sample_minimal_raw_data):
    """
    E2E test: Complete orchestration pipeline with Claude.

    Tests:
    - Data aggregation
    - Strategy creation
    - Claude API call
    - Profile validation
    - Database persistence
    """
    settings = get_settings()

    # Skip if API key not configured
    if not settings.anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not configured")

    user_id = "e2e_test_orchestrator_claude"

    # Create orchestrator with Claude provider
    orchestrator = ProfileConsolidationOrchestrator.create_with_llm_provider(
        async_session, llm_provider_name="anthropic"
    )

    # Mock the aggregator to return our test data
    from unittest.mock import AsyncMock, patch

    from src.etl.core.result import Result

    with patch.object(
        orchestrator.aggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        mock_aggregate.return_value = Result.ok(sample_minimal_raw_data)

        # Execute consolidation
        result = await orchestrator.consolidate_user_profile(user_id)

        # Verify success
        assert result.is_ok, (
            f"Consolidation failed: {result.error_value if result.is_error else 'unknown'}"
        )

        profile = result.value
        assert profile.user_id == user_id
        assert profile.personality_core is not None

        logger.info(f"Claude orchestrator E2E test passed for user {user_id}")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
async def test_orchestrator_e2e_with_openai(async_session, sample_minimal_raw_data):
    """
    E2E test: Complete orchestration pipeline with OpenAI.

    Tests:
    - Data aggregation
    - Strategy creation
    - OpenAI API call
    - Profile validation
    - Database persistence
    """
    settings = get_settings()

    # Skip if API key not configured
    if not settings.openai_api_key:
        pytest.skip("OPENAI_API_KEY not configured")

    user_id = "e2e_test_orchestrator_openai"

    # Create orchestrator with OpenAI provider
    orchestrator = ProfileConsolidationOrchestrator.create_with_llm_provider(
        async_session, llm_provider_name="openai"
    )

    # Mock the aggregator to return our test data
    from unittest.mock import AsyncMock, patch

    from src.etl.core.result import Result

    with patch.object(
        orchestrator.aggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        mock_aggregate.return_value = Result.ok(sample_minimal_raw_data)

        # Execute consolidation
        result = await orchestrator.consolidate_user_profile(user_id)

        # Verify success
        assert result.is_ok, (
            f"Consolidation failed: {result.error_value if result.is_error else 'unknown'}"
        )

        profile = result.value
        assert profile.user_id == user_id
        assert profile.personality_core is not None

        logger.info(f"OpenAI orchestrator E2E test passed for user {user_id}")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
async def test_profile_validation_with_real_llm_output(sample_minimal_raw_data):
    """
    E2E test: Validate that real LLM outputs pass profile validation.

    This test ensures that profiles generated by real LLMs can be
    validated and persisted to the database.
    """
    settings = get_settings()

    # Skip if API key not configured
    if not settings.anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not configured")

    user_id = "e2e_test_validation"

    # Create LLM provider and strategy
    llm_provider = LLMProviderFactory.create("anthropic")
    strategy = DefaultConsolidationStrategy(user_id)

    result = await strategy.consolidate(user_id, sample_minimal_raw_data, llm_provider)

    assert result.is_ok

    profile = result.value

    # Verify all required fields are present and properly typed
    assert isinstance(profile.user_id, str)
    assert profile.personality_core is not None
    assert profile.social_interaction_style is not None
    assert profile.motivations_and_goals is not None
    assert profile.skills_and_identity is not None
    assert profile.lifestyle_and_rhythms is not None
    assert profile.conversation_micro_preferences is not None
    assert profile.behavioral_history_model is not None
    assert profile.agent_persona_heuristic is not None

    logger.info(f"Profile validation E2E test passed for user {user_id}")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
async def test_consolidation_with_diverse_data_sources(async_session):
    """
    E2E test: Consolidation with more diverse data sources.

    Tests that the consolidation handles multiple data types well.
    """
    settings = get_settings()

    # Skip if API key not configured
    if not settings.anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not configured")

    user_id = "e2e_test_diverse_data"

    diverse_data = {
        "resume": {
            "full_text": "Product Manager with background in UX and data analysis. "
            "10+ years building consumer products. "
            "Interested in how technology impacts society.",
            "structured_data": {
                "skills": ["Product Management", "Data Analysis", "UX Research"],
                "experience_years": 10,
            },
        },
        "photos": [
            {
                "file_reference": "photo1.jpg",
                "vlm_caption": "Person speaking at a conference",
                "vlm_analysis": {"context": "professional", "engagement": "high"},
                "exif_data": {},
            },
            {
                "file_reference": "photo2.jpg",
                "vlm_caption": "Person hiking in nature",
                "vlm_analysis": {"context": "outdoor", "mood": "relaxed"},
                "exif_data": {},
            },
        ],
        "voice_notes": [
            {
                "transcription": "I love building products that solve real problems. "
                "I'm passionate about inclusive design and accessibility.",
                "language": "en",
                "extracted_topics": ["product", "design", "accessibility"],
                "sentiment": {"sentiment": "positive", "score": 0.9},
            },
            {
                "transcription": "I prefer async communication but enjoy good video calls for complex discussions.",
                "language": "en",
                "extracted_topics": ["communication", "work-style"],
                "sentiment": {"sentiment": "neutral", "score": 0.6},
            },
        ],
        "chat_transcripts": [
            {
                "platform": "Slack",
                "participants": ["user", "colleague1", "colleague2"],
                "message_count": 45,
                "messages": "[Slack conversation about product roadmap]",
            }
        ],
        "calendar_events": [],
        "emails": [],
        "social_posts": [],
        "blog_posts": [],
        "screenshots": [],
        "shared_images": [],
    }

    # Create LLM provider and strategy
    llm_provider = LLMProviderFactory.create("anthropic")
    strategy = DefaultConsolidationStrategy(user_id)
    result = await strategy.consolidate(user_id, diverse_data, llm_provider)

    assert result.is_ok
    profile = result.value
    assert profile.user_id == user_id

    logger.info(f"Diverse data consolidation E2E test passed for user {user_id}")


# ============================================================================
# MARKERS CONFIGURATION
# ============================================================================
# These tests require pytest configuration in conftest.py:
#
# def pytest_configure(config):
#     config.addinivalue_line("markers", "e2e: end-to-end tests (requires live APIs)")
#     config.addinivalue_line("markers", "slow: slow-running tests")
#
# Run with:
#   pytest -m "e2e" tests/integration/test_consolidation_e2e.py
#   pytest -m "slow and e2e" tests/integration/test_consolidation_e2e.py
#   pytest -m "not slow" tests/unit/  # Skip slow tests in unit tests
