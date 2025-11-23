"""
Unit Tests for Profile Consolidation System.

Tests consolidation logic with mocked LLM APIs to ensure:
- Data aggregation works correctly
- Strategies generate valid profiles
- Error handling is robust
- DI pattern enables strategy swapping
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.consolidation.data_aggregator import DataAggregator
from src.consolidation.llm_adapter import (
    LLMProviderFactory,
    parse_json_response,
)
from src.consolidation.orchestrator import ProfileConsolidationOrchestrator
from src.consolidation.strategy import DefaultConsolidationStrategy
from src.etl.core.result import Result


@pytest.fixture
def sample_raw_data():
    """Sample raw user data for consolidation."""
    return {
        "resume": {
            "full_text": "Senior Software Engineer with 5 years experience",
            "structured_data": {
                "skills": ["Python", "JavaScript"],
                "experience_years": 5,
            },
        },
        "photos": [
            {
                "file_reference": "photo1.jpg",
                "vlm_caption": "Person at a coffee shop",
                "vlm_analysis": {"setting": "casual", "mood": "relaxed"},
                "exif_data": {},
            }
        ],
        "voice_notes": [
            {
                "transcription": "I love meeting new people and having interesting conversations",
                "language": "en",
                "extracted_topics": ["social", "relationships"],
                "sentiment": {"sentiment": "positive", "score": 0.8},
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


@pytest.fixture
def sample_consolidated_profile():
    """Sample consolidated profile output from LLM."""
    return {
        "personality_core": {
            "openness": "High - enjoys new experiences",
            "conscientiousness": "High - detail-oriented",
            "extraversion": "High - social and outgoing",
            "agreeableness": "High - cooperative",
            "emotional_stability": "Medium - balanced",
            "social_match_implications": "Good for group activities",
        },
        "social_interaction_style": {
            "preferred_group_size": "Small group",
            "meeting_structure": "Flexible",
            "tone": "Casual",
            "communication_style": "Direct",
            "response_latency": "Quick",
            "conversation_pacing": "Moderate",
            "comfort_zones_and_boundaries": {
                "energy_constraints": "Moderate energy needed",
                "safety_preferences": "Values privacy",
                "time_of_day_comfort": "Flexible",
                "pace_of_progress": "Steady",
                "topics_to_avoid": ["politics"],
            },
        },
        "motivations_and_goals": {
            "primary_goal": "Build meaningful connections",
            "secondary_goal": "Share knowledge",
            "underlying_needs": ["belonging", "growth", "contribution"],
        },
        "skills_and_identity": {
            "skills": ["Python", "JavaScript", "Communication"],
            "skill_levels": {"Python": "Expert", "JavaScript": "Advanced"},
            "experience": "5+ years in software engineering",
            "identity_tags": ["Engineer", "Mentor", "Social"],
        },
        "lifestyle_and_rhythms": {
            "availability": {
                "weekday_evenings": "Available",
                "weekend_mornings": "Available",
            },
            "weekly_rhythm": "Stable routine",
            "preferred_locations": ["Coffee shops", "Tech meetups"],
            "mobility": {
                "preferred_radius_km": 15,
                "transport_modes": ["Walking", "Public transit"],
            },
            "environmental_context": {
                "local_area_familiarity": "High",
                "high_density_areas_exposure": "Comfortable",
            },
        },
        "conversation_micro_preferences": {
            "preferred_opener_style": "Question",
            "emoji_usage": "Moderate",
            "humor_style": "Witty",
            "formality_level": "Casual",
            "preferred_medium": "Text",
            "default_tone": "Friendly",
        },
        "behavioral_history_model": {
            "match_acceptance_pattern": "Accepts good conversational matches",
            "match_decline_pattern": "Declines topic mismatches",
            "good_outcomes_pattern": "Shared interests lead to good outcomes",
            "response_latency_pattern": "Quick responses within hours",
            "conversation_patterns": "Initiates questions, maintains flow",
        },
        "agent_persona_heuristic": {
            "voice": "Friendly and professional",
            "decision_priorities": {"compatibility": 0.6, "availability": 0.4},
            "tone_guidance": "Warm and genuine",
            "risk_tolerance": "Medium",
            "serendipity_openness": "Open to surprises",
        },
    }


# ============================================================================
# DATA AGGREGATOR TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_data_aggregator_with_complete_data(db_session):
    """Test aggregator retrieves all available data types."""
    aggregator = DataAggregator(db_session)
    user_id = "test_user_complete"

    # Mock database queries
    with patch.object(
        aggregator, "_get_resume_data", new_callable=AsyncMock
    ) as mock_resume:
        with patch.object(
            aggregator, "_get_photo_data", new_callable=AsyncMock
        ) as mock_photos:
            mock_resume.return_value = {"full_text": "test resume"}
            mock_photos.return_value = [{"caption": "test photo"}]

            result = await aggregator.aggregate_user_data(user_id)

            assert result.is_ok
            data = result.value
            assert data["resume"] == {"full_text": "test resume"}
            assert data["photos"] == [{"caption": "test photo"}]


@pytest.mark.asyncio
async def test_data_aggregator_with_partial_data(db_session):
    """Test aggregator handles incomplete data gracefully."""
    aggregator = DataAggregator(db_session)
    user_id = "test_user_partial"

    with patch.object(
        aggregator, "_get_resume_data", new_callable=AsyncMock
    ) as mock_resume:
        with patch.object(
            aggregator, "_get_photo_data", new_callable=AsyncMock
        ) as mock_photos:
            with patch.object(
                aggregator, "_get_voice_note_data", new_callable=AsyncMock
            ) as mock_voice:
                mock_resume.return_value = None
                mock_photos.return_value = []
                mock_voice.return_value = [{"transcription": "test"}]

                result = await aggregator.aggregate_user_data(user_id)

                assert result.is_ok
                data = result.value
                assert data["resume"] is None
                assert data["photos"] == []
                assert data["voice_notes"] == [{"transcription": "test"}]


@pytest.mark.asyncio
async def test_data_aggregator_error_handling(db_session):
    """Test aggregator handles database errors gracefully."""
    aggregator = DataAggregator(db_session)
    user_id = "test_user_error"

    # Mock a database error
    with patch.object(
        aggregator, "_get_resume_data", new_callable=AsyncMock
    ) as mock_resume:
        mock_resume.side_effect = Exception("Database error")

        result = await aggregator.aggregate_user_data(user_id)

        assert result.is_error
        assert isinstance(result.error_value, Exception)


# ============================================================================
# STRATEGY AND LLM PROVIDER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_consolidation_strategy_with_valid_data(
    sample_raw_data, sample_consolidated_profile
):
    """Test consolidation strategy with mocked LLM provider."""
    user_id = "test_user_strategy"

    # Create mock LLM provider
    mock_llm_provider = MagicMock()
    mock_llm_provider.call = AsyncMock(
        return_value=json.dumps(sample_consolidated_profile)
    )
    mock_llm_provider.get_provider_name = MagicMock(return_value="anthropic")

    # Create strategy with injected provider
    strategy = DefaultConsolidationStrategy(user_id)

    result = await strategy.consolidate(user_id, sample_raw_data, mock_llm_provider)

    assert result.is_ok
    profile = result.value
    assert profile.user_id == user_id
    assert profile.personality_core.openness == "High - enjoys new experiences"
    assert profile.social_interaction_style.preferred_group_size == "Small group"


@pytest.mark.asyncio
async def test_consolidation_strategy_with_empty_data():
    """Test consolidation strategy rejects empty data."""
    user_id = "test_user_empty"

    mock_llm_provider = MagicMock()
    strategy = DefaultConsolidationStrategy(user_id)

    empty_data = {
        "resume": None,
        "photos": [],
        "voice_notes": [],
        "chat_transcripts": [],
        "calendar_events": [],
        "emails": [],
        "social_posts": [],
        "blog_posts": [],
        "screenshots": [],
        "shared_images": [],
    }

    result = await strategy.consolidate(user_id, empty_data, mock_llm_provider)

    assert result.is_error
    assert "No user data available" in str(result.error_value)


@pytest.mark.asyncio
async def test_llm_json_response_parsing():
    """Test JSON response parsing from LLM."""
    # Test valid JSON parsing
    valid_json = '{"personality_core": {"openness": "High"}}'
    result = parse_json_response(valid_json)
    assert result["personality_core"]["openness"] == "High"

    # Test JSON extraction from text
    text_with_json = (
        'Here is the profile: {"personality_core": {"openness": "High"}} done'
    )
    result = parse_json_response(text_with_json)
    assert result["personality_core"]["openness"] == "High"

    # Test invalid JSON raises error
    with pytest.raises(ValueError):
        parse_json_response("This is not JSON at all")


@pytest.mark.asyncio
async def test_consolidation_strategy_invalid_response(sample_raw_data):
    """Test consolidation strategy handles invalid LLM response."""
    user_id = "test_user_invalid"

    mock_llm_provider = MagicMock()
    mock_llm_provider.call = AsyncMock(return_value="Invalid response, not JSON")
    mock_llm_provider.get_provider_name = MagicMock(return_value="anthropic")

    strategy = DefaultConsolidationStrategy(user_id)
    result = await strategy.consolidate(user_id, sample_raw_data, mock_llm_provider)

    assert result.is_error


# ============================================================================
# LLM PROVIDER FACTORY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_consolidation_with_different_llm_providers(
    sample_raw_data, sample_consolidated_profile
):
    """Test consolidation strategy works with different LLM providers."""
    user_id = "test_user_providers"

    # Test with Anthropic provider mock
    anthropic_provider = MagicMock()
    anthropic_provider.call = AsyncMock(
        return_value=json.dumps(sample_consolidated_profile)
    )
    anthropic_provider.get_provider_name = MagicMock(return_value="anthropic")

    strategy = DefaultConsolidationStrategy(user_id)
    result = await strategy.consolidate(user_id, sample_raw_data, anthropic_provider)

    assert result.is_ok
    assert result.value.user_id == user_id

    # Test with OpenAI provider mock
    openai_provider = MagicMock()
    openai_provider.call = AsyncMock(
        return_value=json.dumps(sample_consolidated_profile)
    )
    openai_provider.get_provider_name = MagicMock(return_value="openai")

    result = await strategy.consolidate(user_id, sample_raw_data, openai_provider)

    assert result.is_ok
    assert result.value.user_id == user_id


@pytest.mark.asyncio
async def test_llm_provider_factory_creates_providers():
    """Test LLM provider factory creates correct provider instances."""
    # Factory method should create providers without errors
    anthropic_provider = LLMProviderFactory.create("anthropic")
    assert anthropic_provider is not None
    assert anthropic_provider.get_provider_name() == "anthropic"

    openai_provider = LLMProviderFactory.create("openai")
    assert openai_provider is not None
    assert openai_provider.get_provider_name() == "openai"

    # Test invalid provider raises error
    with pytest.raises(ValueError):
        LLMProviderFactory.create("invalid_provider")


# ============================================================================
# ORCHESTRATOR TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrator_with_injected_strategy(db_session, sample_raw_data):
    """Test orchestrator accepts injected strategy via DI."""
    user_id = "test_user_di"

    # Create mock strategy
    mock_strategy = AsyncMock()
    mock_strategy.consolidate = AsyncMock(
        return_value=Result.ok(MagicMock(spec=object))
    )

    with patch.object(
        DataAggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        with patch.object(
            ProfileConsolidationOrchestrator, "_persist_profile", new_callable=AsyncMock
        ) as mock_persist:
            mock_aggregate.return_value = Result.ok(sample_raw_data)
            mock_persist.return_value = Result.ok(MagicMock())

            orchestrator = ProfileConsolidationOrchestrator.create_with_strategy(
                db_session, mock_strategy
            )

            result = await orchestrator.consolidate_user_profile(user_id)

            assert result.is_ok
            mock_strategy.consolidate.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_with_llm_provider_selection(db_session, sample_raw_data):
    """Test orchestrator supports LLM provider-based strategy selection."""
    user_id = "test_user_provider"

    with patch.object(
        DataAggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        with patch.object(
            DefaultConsolidationStrategy, "consolidate", new_callable=AsyncMock
        ) as mock_consolidate:
            with patch.object(
                ProfileConsolidationOrchestrator,
                "_persist_profile",
                new_callable=AsyncMock,
            ) as mock_persist:
                mock_aggregate.return_value = Result.ok(sample_raw_data)
                mock_profile = MagicMock()
                mock_profile.user_id = user_id
                mock_consolidate.return_value = Result.ok(mock_profile)
                mock_persist.return_value = Result.ok(mock_profile)

                # Test with Anthropic provider
                orchestrator = (
                    ProfileConsolidationOrchestrator.create_with_llm_provider(
                        db_session, llm_provider_name="anthropic"
                    )
                )
                result = await orchestrator.consolidate_user_profile(user_id)

                assert result.is_ok

                # Test with OpenAI provider
                orchestrator = (
                    ProfileConsolidationOrchestrator.create_with_llm_provider(
                        db_session, llm_provider_name="openai"
                    )
                )
                result = await orchestrator.consolidate_user_profile(user_id)
                assert result.is_ok


@pytest.mark.asyncio
async def test_orchestrator_aggregation_error(db_session):
    """Test orchestrator handles aggregation errors."""
    user_id = "test_user_agg_error"

    with patch.object(
        DataAggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        mock_aggregate.return_value = Result.error(Exception("Aggregation failed"))

        orchestrator = ProfileConsolidationOrchestrator.create_with_llm_provider(
            db_session
        )
        result = await orchestrator.consolidate_user_profile(user_id)

        assert result.is_error
        assert "Aggregation failed" in str(result.error_value)


@pytest.mark.asyncio
async def test_orchestrator_consolidation_error(db_session, sample_raw_data):
    """Test orchestrator handles consolidation strategy errors."""
    user_id = "test_user_cons_error"

    # Create mock strategy that fails
    mock_strategy = AsyncMock()
    mock_strategy.consolidate = AsyncMock(
        return_value=Result.error(Exception("LLM consolidation failed"))
    )

    with patch.object(
        DataAggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        mock_aggregate.return_value = Result.ok(sample_raw_data)

        orchestrator = ProfileConsolidationOrchestrator.create_with_strategy(
            db_session, mock_strategy
        )

        result = await orchestrator.consolidate_user_profile(user_id)

        assert result.is_error


@pytest.mark.asyncio
async def test_orchestrator_persistence_error(db_session, sample_raw_data):
    """Test orchestrator handles persistence errors."""
    user_id = "test_user_persist_error"

    with patch.object(
        DataAggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        with patch.object(
            DefaultConsolidationStrategy, "consolidate", new_callable=AsyncMock
        ) as mock_consolidate:
            with patch.object(
                ProfileConsolidationOrchestrator,
                "_persist_profile",
                new_callable=AsyncMock,
            ) as mock_persist:
                mock_aggregate.return_value = Result.ok(sample_raw_data)
                mock_profile = MagicMock()
                mock_consolidate.return_value = Result.ok(mock_profile)
                mock_persist.return_value = Result.error(Exception("Database error"))

                orchestrator = (
                    ProfileConsolidationOrchestrator.create_with_llm_provider(
                        db_session
                    )
                )
                result = await orchestrator.consolidate_user_profile(user_id)

                assert result.is_error
                assert "Database error" in str(result.error_value)


# ============================================================================
# INTEGRATION-LIKE TESTS (UNIT BUT COMPREHENSIVE)
# ============================================================================


@pytest.mark.asyncio
async def test_consolidation_pipeline_happy_path(db_session, sample_raw_data):
    """Test complete consolidation pipeline with mocked LLM."""
    user_id = "test_user_happy"

    with patch.object(
        DataAggregator, "aggregate_user_data", new_callable=AsyncMock
    ) as mock_aggregate:
        with patch.object(
            DefaultConsolidationStrategy, "consolidate", new_callable=AsyncMock
        ) as mock_consolidate:
            with patch.object(
                ProfileConsolidationOrchestrator,
                "_persist_profile",
                new_callable=AsyncMock,
            ) as mock_persist:
                # Setup mocks
                mock_aggregate.return_value = Result.ok(sample_raw_data)

                mock_profile = MagicMock()
                mock_profile.user_id = user_id
                mock_consolidate.return_value = Result.ok(mock_profile)
                mock_persist.return_value = Result.ok(mock_profile)

                # Execute pipeline
                orchestrator = (
                    ProfileConsolidationOrchestrator.create_with_llm_provider(
                        db_session, llm_provider_name="anthropic"
                    )
                )
                result = await orchestrator.consolidate_user_profile(user_id)

                # Verify success
                assert result.is_ok
                mock_aggregate.assert_called_once()
                mock_consolidate.assert_called_once()
                mock_persist.assert_called_once()
