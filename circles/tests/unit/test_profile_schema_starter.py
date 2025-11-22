"""
Starter unit tests for profile schema validation.

This file provides initial test examples to get started with testing.
Copy and expand these patterns to achieve full coverage.
"""

import pytest
from pydantic import ValidationError

from circles.src.profile_schema import (
    AgentPersonaHeuristic,
    Availability,
    BehaviouralHistoryModel,
    ComfortZonesAndBoundaries,
    ConversationMicroPreferences,
    EnvironmentalContext,
    LifestyleAndRhythms,
    Mobility,
    MotivationsAndGoals,
    PersonalityCore,
    SkillsAndIdentity,
    SocialInteractionStyle,
    UserProfile,
)

# ============================================================================
# PersonalityCore Tests
# ============================================================================


class TestPersonalityCore:
    """Test suite for PersonalityCore Pydantic model."""

    def test_valid_personality_core(self):
        """Test creating PersonalityCore with all valid fields."""
        core = PersonalityCore(
            openness="High",
            conscientiousness="Medium",
            extraversion="Low",
            agreeableness="High",
            emotional_stability="Medium",
            social_match_implications="Compatible with analytical, low-key partners",
        )

        assert core.openness == "High"
        assert core.conscientiousness == "Medium"
        assert core.extraversion == "Low"
        assert isinstance(core.social_match_implications, str)

    def test_personality_core_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalityCore(
                openness="High",
                conscientiousness="Medium",
                # Missing: extraversion, agreeableness, emotional_stability, social_match_implications
            )

        errors = exc_info.value.errors()
        assert len(errors) == 4  # 4 missing fields
        field_names = {error["loc"][0] for error in errors}
        assert "extraversion" in field_names
        assert "agreeableness" in field_names
        assert "emotional_stability" in field_names
        assert "social_match_implications" in field_names

    def test_personality_core_empty_strings(self):
        """Test that empty strings are accepted (no minimum length constraint)."""
        core = PersonalityCore(
            openness="",
            conscientiousness="",
            extraversion="",
            agreeableness="",
            emotional_stability="",
            social_match_implications="",
        )

        assert core.openness == ""
        assert core.social_match_implications == ""

    def test_personality_core_very_long_text(self):
        """Test handling of very long text in implications field."""
        long_text = "x" * 10000  # 10k characters

        core = PersonalityCore(
            openness="High",
            conscientiousness="Medium",
            extraversion="Low",
            agreeableness="High",
            emotional_stability="Medium",
            social_match_implications=long_text,
        )

        assert len(core.social_match_implications) == 10000

    def test_personality_core_special_characters(self):
        """Test handling of special characters and Unicode."""
        core = PersonalityCore(
            openness="High",
            conscientiousness="Medium 中文",
            extraversion="Low émojis 😊",
            agreeableness="High <script>alert('xss')</script>",
            emotional_stability="Medium ñ ü",
            social_match_implications="Compatible with 日本語 users & 'special' chars",
        )

        assert "中文" in core.conscientiousness
        assert "😊" in core.extraversion
        assert "<script>" in core.agreeableness  # Should be stored as-is

    def test_personality_core_to_dict(self):
        """Test conversion to dictionary."""
        core = PersonalityCore(
            openness="High",
            conscientiousness="Medium",
            extraversion="Low",
            agreeableness="High",
            emotional_stability="Medium",
            social_match_implications="Test",
        )

        data = core.model_dump()

        assert isinstance(data, dict)
        assert data["openness"] == "High"
        assert data["conscientiousness"] == "Medium"
        assert len(data) == 6


# ============================================================================
# ComfortZonesAndBoundaries Tests
# ============================================================================


class TestComfortZonesAndBoundaries:
    """Test suite for ComfortZonesAndBoundaries model."""

    def test_valid_comfort_zones(self):
        """Test creating ComfortZonesAndBoundaries with valid data."""
        zones = ComfortZonesAndBoundaries(
            energy_constraints="Low social battery, prefers 1-2 meetups per week",
            safety_preferences="Public places only, well-lit areas",
            time_of_day_comfort="Evenings after 18:00, weekend mornings",
            pace_of_progress="Medium - willing to meet within a week",
            topics_to_avoid=["politics", "religion", "personal finances"],
        )

        assert zones.energy_constraints.startswith("Low")
        assert len(zones.topics_to_avoid) == 3
        assert "politics" in zones.topics_to_avoid

    def test_comfort_zones_empty_topics_list(self):
        """Test that empty topics_to_avoid list is valid."""
        zones = ComfortZonesAndBoundaries(
            energy_constraints="High energy",
            safety_preferences="Flexible",
            time_of_day_comfort="Anytime",
            pace_of_progress="Fast",
            topics_to_avoid=[],
        )

        assert zones.topics_to_avoid == []
        assert isinstance(zones.topics_to_avoid, list)

    def test_comfort_zones_duplicate_topics(self):
        """Test handling of duplicate topics in list."""
        zones = ComfortZonesAndBoundaries(
            energy_constraints="Medium",
            safety_preferences="Standard",
            time_of_day_comfort="Flexible",
            pace_of_progress="Medium",
            topics_to_avoid=["politics", "politics", "religion"],
        )

        # Pydantic doesn't deduplicate by default
        assert len(zones.topics_to_avoid) == 3
        assert zones.topics_to_avoid.count("politics") == 2

    def test_comfort_zones_very_long_topic_list(self):
        """Test with many topics to avoid."""
        topics = [f"topic_{i}" for i in range(100)]

        zones = ComfortZonesAndBoundaries(
            energy_constraints="Low",
            safety_preferences="High",
            time_of_day_comfort="Limited",
            pace_of_progress="Slow",
            topics_to_avoid=topics,
        )

        assert len(zones.topics_to_avoid) == 100


# ============================================================================
# SocialInteractionStyle Tests
# ============================================================================


class TestSocialInteractionStyle:
    """Test suite for SocialInteractionStyle with nested models."""

    def test_valid_social_interaction_style(self):
        """Test creating SocialInteractionStyle with nested ComfortZones."""
        comfort_zones = ComfortZonesAndBoundaries(
            energy_constraints="Medium",
            safety_preferences="Public places",
            time_of_day_comfort="Evenings",
            pace_of_progress="Medium",
            topics_to_avoid=["politics"],
        )

        style = SocialInteractionStyle(
            preferred_group_size="1:1 or small group (2-3)",
            meeting_structure="Structured with clear agenda",
            tone="Friendly and analytical",
            communication_style="Medium-length messages",
            response_latency="2-3 hours",
            conversation_pacing="Steady, leading to concrete plans",
            comfort_zones_and_boundaries=comfort_zones,
        )

        assert style.preferred_group_size.startswith("1:1")
        assert isinstance(style.comfort_zones_and_boundaries, ComfortZonesAndBoundaries)
        assert style.comfort_zones_and_boundaries.pace_of_progress == "Medium"

    def test_social_interaction_nested_validation_error(self):
        """Test that nested model validation errors propagate correctly."""
        with pytest.raises(ValidationError) as exc_info:
            SocialInteractionStyle(
                preferred_group_size="Small",
                meeting_structure="Flexible",
                tone="Casual",
                communication_style="Brief",
                response_latency="Fast",
                conversation_pacing="Quick",
                comfort_zones_and_boundaries=ComfortZonesAndBoundaries(
                    energy_constraints="Low",
                    # Missing required fields
                ),
            )

        errors = exc_info.value.errors()
        # Should have errors for missing fields in nested model
        assert len(errors) > 0

    def test_social_interaction_emoji_handling(self):
        """Test handling of emojis in communication style."""
        comfort_zones = ComfortZonesAndBoundaries(
            energy_constraints="Medium",
            safety_preferences="Public",
            time_of_day_comfort="Flexible",
            pace_of_progress="Medium",
            topics_to_avoid=[],
        )

        style = SocialInteractionStyle(
            preferred_group_size="1:1 😊",
            meeting_structure="Casual ☕",
            tone="Friendly 👋",
            communication_style="Uses emojis 😄👍",
            response_latency="Quick ⚡",
            conversation_pacing="Energetic 🚀",
            comfort_zones_and_boundaries=comfort_zones,
        )

        assert "😊" in style.preferred_group_size
        assert "🚀" in style.conversation_pacing


# ============================================================================
# MotivationsAndGoals Tests
# ============================================================================


class TestMotivationsAndGoals:
    """Test suite for MotivationsAndGoals model."""

    def test_valid_motivations_and_goals(self):
        """Test creating MotivationsAndGoals with valid data."""
        motivations = MotivationsAndGoals(
            primary_goal="Find tech meetup partners in Santiago",
            secondary_goal="Practice conversational Spanish",
            underlying_needs=["growth", "relatedness", "autonomy"],
        )

        assert "Santiago" in motivations.primary_goal
        assert len(motivations.underlying_needs) == 3
        assert "growth" in motivations.underlying_needs

    def test_motivations_empty_underlying_needs(self):
        """Test with empty underlying needs list."""
        motivations = MotivationsAndGoals(
            primary_goal="Main goal",
            secondary_goal="Secondary goal",
            underlying_needs=[],
        )

        assert motivations.underlying_needs == []

    def test_motivations_very_long_goal_text(self):
        """Test with very long goal descriptions."""
        long_goal = "x" * 5000

        motivations = MotivationsAndGoals(
            primary_goal=long_goal, secondary_goal=long_goal, underlying_needs=["test"]
        )

        assert len(motivations.primary_goal) == 5000
        assert len(motivations.secondary_goal) == 5000


# ============================================================================
# SkillsAndIdentity Tests
# ============================================================================


class TestSkillsAndIdentity:
    """Test suite for SkillsAndIdentity model."""

    def test_valid_skills_and_identity(self):
        """Test creating SkillsAndIdentity with valid data."""
        skills = SkillsAndIdentity(
            skills=["Python", "JavaScript", "React"],
            skill_levels={
                "Python": "Advanced",
                "JavaScript": "Intermediate",
                "React": "Beginner",
            },
            experience="5+ years in software development",
            identity_tags=["Developer", "Maker", "Remote worker"],
        )

        assert len(skills.skills) == 3
        assert skills.skill_levels["Python"] == "Advanced"
        assert "Developer" in skills.identity_tags

    def test_skills_empty_lists(self):
        """Test with empty skills and identity tags lists."""
        skills = SkillsAndIdentity(
            skills=[],
            skill_levels={},
            experience="No formal experience",
            identity_tags=[],
        )

        assert skills.skills == []
        assert skills.skill_levels == {}
        assert skills.identity_tags == []

    def test_skills_dict_type_validation(self):
        """Test that skill_levels dict accepts string values."""
        skills = SkillsAndIdentity(
            skills=["Python"],
            skill_levels={"Python": "Advanced"},
            experience="Expert",
            identity_tags=["Coder"],
        )

        assert isinstance(skills.skill_levels, dict)
        assert isinstance(skills.skill_levels["Python"], str)

    def test_skills_duplicate_entries(self):
        """Test handling of duplicate skills."""
        skills = SkillsAndIdentity(
            skills=["Python", "Python", "JavaScript"],
            skill_levels={"Python": "Advanced"},
            experience="Test",
            identity_tags=["Dev", "Dev"],
        )

        # Pydantic doesn't deduplicate lists by default
        assert len(skills.skills) == 3
        assert skills.skills.count("Python") == 2


# ============================================================================
# Mobility Tests
# ============================================================================


class TestMobility:
    """Test suite for Mobility model."""

    def test_valid_mobility(self):
        """Test creating Mobility with valid data."""
        mobility = Mobility(
            preferred_radius_km=5, transport_modes=["walk", "bike", "public transport"]
        )

        assert mobility.preferred_radius_km == 5
        assert len(mobility.transport_modes) == 3

    def test_mobility_zero_radius(self):
        """Test that zero radius is accepted (edge case)."""
        mobility = Mobility(preferred_radius_km=0, transport_modes=["walk"])

        assert mobility.preferred_radius_km == 0

    def test_mobility_large_radius(self):
        """Test with very large radius value."""
        mobility = Mobility(
            preferred_radius_km=999999, transport_modes=["car", "plane"]
        )

        assert mobility.preferred_radius_km == 999999

    def test_mobility_empty_transport_modes(self):
        """Test with empty transport modes list."""
        mobility = Mobility(preferred_radius_km=10, transport_modes=[])

        assert mobility.transport_modes == []


# ============================================================================
# UserProfile Tests (Basic)
# ============================================================================


class TestUserProfileBasic:
    """Basic tests for UserProfile SQLModel - no database required."""

    def test_user_profile_model_instantiation(self):
        """Test that UserProfile can be instantiated with all required fields."""
        # Note: This test doesn't save to database, just validates model structure

        personality_core = PersonalityCore(
            openness="High",
            conscientiousness="Medium",
            extraversion="Low",
            agreeableness="High",
            emotional_stability="Medium",
            social_match_implications="Test",
        )

        comfort_zones = ComfortZonesAndBoundaries(
            energy_constraints="Medium",
            safety_preferences="Public",
            time_of_day_comfort="Evenings",
            pace_of_progress="Medium",
            topics_to_avoid=[],
        )

        social_style = SocialInteractionStyle(
            preferred_group_size="1:1",
            meeting_structure="Flexible",
            tone="Casual",
            communication_style="Brief",
            response_latency="Fast",
            conversation_pacing="Quick",
            comfort_zones_and_boundaries=comfort_zones,
        )

        motivations = MotivationsAndGoals(
            primary_goal="Test goal",
            secondary_goal="Test secondary",
            underlying_needs=["test"],
        )

        skills = SkillsAndIdentity(
            skills=["Python"],
            skill_levels={"Python": "Advanced"},
            experience="5 years",
            identity_tags=["Developer"],
        )

        availability = Availability(
            weekday_evenings="18:00-21:00", weekend_mornings="09:00-12:00"
        )

        mobility = Mobility(preferred_radius_km=5, transport_modes=["bike"])

        env_context = EnvironmentalContext(
            local_area_familiarity="High", high_density_areas_exposure="Medium"
        )

        lifestyle = LifestyleAndRhythms(
            availability=availability,
            weekly_rhythm="Work-focused weekdays",
            mobility=mobility,
            preferred_locations=["Cafes"],
            environmental_context=env_context,
        )

        conversation_prefs = ConversationMicroPreferences(
            preferred_opener_style="Casual",
            emoji_usage="Light",
            humor_style="Dry",
            formality_level="Informal",
            preferred_medium="Chat",
            default_tone="Friendly",
        )

        behavioural_history = BehaviouralHistoryModel(
            match_acceptance_pattern="Test pattern",
            match_decline_pattern="Test decline",
            good_outcomes_pattern="Test outcomes",
            response_latency_pattern="Test latency",
            conversation_patterns="Test conversation",
        )

        agent_persona = AgentPersonaHeuristic(
            voice="Friendly",
            decision_priorities={"1": "Priority one", "2": "Priority two"},
            tone_guidance="Casual and helpful",
            risk_tolerance="Medium",
            serendipity_openness="High",
        )

        # Create UserProfile instance (without saving to database)
        profile = UserProfile(
            user_id="550e8400-e29b-41d4-a716-446655440001",
            personality_core=personality_core,
            social_interaction_style=social_style,
            motivations_and_goals=motivations,
            skills_and_identity=skills,
            lifestyle_and_rhythms=lifestyle,
            conversation_micro_preferences=conversation_prefs,
            behavioural_history_model=behavioural_history,
            agent_persona_heuristic=agent_persona,
            is_active=True,
        )

        # Assertions
        assert profile.user_id == "550e8400-e29b-41d4-a716-446655440001"
        assert profile.is_active is True
        assert profile.personality_core.openness == "High"
        assert profile.social_interaction_style.preferred_group_size == "1:1"
        assert profile.motivations_and_goals.primary_goal == "Test goal"
        assert profile.skills_and_identity.skills[0] == "Python"

    def test_user_profile_default_values(self):
        """Test that default values are set correctly."""
        # Create minimal profile to test defaults
        profile = UserProfile(
            user_id="550e8400-e29b-41d4-a716-446655440002",
            personality_core=PersonalityCore(
                openness="H",
                conscientiousness="M",
                extraversion="L",
                agreeableness="H",
                emotional_stability="M",
                social_match_implications="T",
            ),
            # ... (abbreviated for brevity, would include all required fields)
        )

        # Test defaults
        assert profile.id is None  # Not set until saved to database
        assert profile.is_active is True  # Default value
        assert profile.last_matched is None  # Default value


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_personality_core_unicode_support(self):
        """Test full Unicode support across all languages."""
        core = PersonalityCore(
            openness="高い (High)",
            conscientiousness="Высокий (High)",
            extraversion="عالي (High)",
            agreeableness="גבוה (High)",
            emotional_stability="높은 (High)",
            social_match_implications="Compatible avec tous les utilisateurs",
        )

        assert "高い" in core.openness
        assert "Высокий" in core.conscientiousness
        assert "عالي" in core.extraversion

    def test_all_models_json_serializable(self):
        """Test that all models can be serialized to JSON."""
        models = [
            PersonalityCore(
                openness="H",
                conscientiousness="M",
                extraversion="L",
                agreeableness="H",
                emotional_stability="M",
                social_match_implications="T",
            ),
            ComfortZonesAndBoundaries(
                energy_constraints="T",
                safety_preferences="T",
                time_of_day_comfort="T",
                pace_of_progress="T",
                topics_to_avoid=[],
            ),
            MotivationsAndGoals(
                primary_goal="T", secondary_goal="T", underlying_needs=[]
            ),
            Mobility(preferred_radius_km=5, transport_modes=["walk"]),
        ]

        for model in models:
            json_data = model.model_dump_json()
            assert isinstance(json_data, str)
            assert len(json_data) > 0


# ============================================================================
# Parametrized Tests Example
# ============================================================================


class TestParametrized:
    """Example of parametrized tests for efficiency."""

    @pytest.mark.parametrize(
        "openness,expected",
        [
            ("Low", "Low"),
            ("Medium", "Medium"),
            ("High", "High"),
            ("Medium-High", "Medium-High"),
            ("", ""),
        ],
    )
    def test_personality_openness_values(self, openness, expected):
        """Test various openness values are accepted."""
        core = PersonalityCore(
            openness=openness,
            conscientiousness="Medium",
            extraversion="Medium",
            agreeableness="Medium",
            emotional_stability="Medium",
            social_match_implications="Test",
        )
        assert core.openness == expected

    @pytest.mark.parametrize("radius", [0, 1, 5, 10, 50, 100, 999999])
    def test_mobility_radius_values(self, radius):
        """Test various radius values are accepted."""
        mobility = Mobility(preferred_radius_km=radius, transport_modes=["walk"])
        assert mobility.preferred_radius_km == radius

    @pytest.mark.parametrize(
        "topics",
        [
            [],
            ["one"],
            ["one", "two"],
            ["one", "two", "three", "four", "five"],
            [f"topic_{i}" for i in range(100)],
        ],
    )
    def test_comfort_zones_topics_variations(self, topics):
        """Test various topics_to_avoid list sizes."""
        zones = ComfortZonesAndBoundaries(
            energy_constraints="T",
            safety_preferences="T",
            time_of_day_comfort="T",
            pace_of_progress="T",
            topics_to_avoid=topics,
        )
        assert len(zones.topics_to_avoid) == len(topics)


# ============================================================================
# Performance Indicator Tests
# ============================================================================


class TestPerformance:
    """Basic performance indicator tests (not comprehensive benchmarks)."""

    def test_create_1000_personality_cores(self):
        """Test that creating 1000 PersonalityCore instances is fast."""
        import time

        start = time.time()
        cores = []
        for i in range(1000):
            core = PersonalityCore(
                openness="High",
                conscientiousness="Medium",
                extraversion="Low",
                agreeableness="High",
                emotional_stability="Medium",
                social_match_implications=f"User {i} implications",
            )
            cores.append(core)
        elapsed = time.time() - start

        assert len(cores) == 1000
        assert elapsed < 1.0  # Should complete in under 1 second

    def test_json_serialization_performance(self):
        """Test JSON serialization performance."""
        import time

        core = PersonalityCore(
            openness="High",
            conscientiousness="Medium",
            extraversion="Low",
            agreeableness="High",
            emotional_stability="Medium",
            social_match_implications="Test" * 100,
        )

        start = time.time()
        for _ in range(1000):
            _ = core.model_dump_json()
        elapsed = time.time() - start

        assert elapsed < 1.0  # 1000 serializations in under 1 second
