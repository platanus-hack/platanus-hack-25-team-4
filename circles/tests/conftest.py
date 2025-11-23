"""
Pytest configuration and shared fixtures.

This file contains test configuration and fixtures that are available
to all test files in the test suite.

Fixtures are organized into sections:
1. Test Database Configuration (async and sync)
2. Redis Configuration
3. Celery Configuration
4. File Storage Configuration
5. Sample Data Fixtures (Profile Schema)
6. Factory Fixtures
7. Cleanup and Utility Fixtures
8. Marker Configuration
"""

import os
from datetime import datetime

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from src.profile_schema import (
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

# Try to import async test utilities
try:
    import pytest_asyncio

    HAS_PYTEST_ASYNCIO = True
except ImportError:
    HAS_PYTEST_ASYNCIO = False

    # Provide a no-op decorator if pytest_asyncio is not available
    class _NoOpAsyncio:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

    pytest_asyncio = _NoOpAsyncio()

try:
    from fakeredis import FakeStrictRedis
except ImportError:
    FakeStrictRedis = None

try:
    from celery import Celery
    from celery.result import EagerResult
except ImportError:
    Celery = None

# Load test settings
from tests.config.test_settings import get_test_settings

test_settings = get_test_settings()


# ============================================================================
# Test Database Configuration (Async)
# ============================================================================


@pytest_asyncio.fixture
async def async_engine():
    """
    Create an async PostgreSQL engine for testing.

    Uses the test database configured in test_settings with proper
    async connection pooling.
    """
    engine = create_async_engine(
        test_settings.get_database_url(),
        echo=False,
        pool_size=test_settings.test_database_pool_size,
        max_overflow=test_settings.test_database_max_overflow,
        pool_pre_ping=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session with transaction rollback.

    Each test gets a fresh transaction that rolls back after the test,
    ensuring complete isolation.
    """
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session_factory() as session:
        async with session.begin():
            yield session
            # Transaction rolls back automatically


# ============================================================================
# Test Database Configuration (Sync - Legacy Support)
# ============================================================================


@pytest.fixture(scope="function")
def test_engine():
    """
    Create an in-memory SQLite engine for testing.

    Uses a separate in-memory database for each test function to ensure
    test isolation. The StaticPool ensures the connection stays open for
    the duration of the test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """
    Create all database tables for testing.

    This fixture creates a fresh database schema for each test,
    ensuring complete isolation between tests.
    """
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def db_session(test_db):
    """
    Provide a database session for tests.

    The session automatically rolls back after each test to ensure
    test isolation, even if the test doesn't explicitly clean up.
    """
    connection = test_db.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ============================================================================
# Redis Configuration
# ============================================================================


@pytest.fixture
def redis_url() -> str:
    """
    Get the test Redis URL from settings.

    Can be overridden via environment variable TEST_REDIS_URL.
    """
    return test_settings.get_redis_url()


@pytest.fixture
def redis_client():
    """
    Provide a Redis client for testing.

    Uses fakeredis by default (faster, no external dependency) or
    real Redis if TEST_USE_REAL_REDIS=true.
    """
    if test_settings.use_real_redis:
        try:
            import redis

            client = redis.Redis.from_url(test_settings.get_redis_url())
            client.ping()
            yield client
            client.flushdb()
        except Exception as e:
            pytest.skip(f"Real Redis not available: {e}")
    else:
        # Use fakeredis for speed
        if FakeStrictRedis is None:
            pytest.skip("fakeredis not installed")
        client = FakeStrictRedis()
        yield client
        client.flushdb()


# ============================================================================
# Celery Configuration
# ============================================================================


@pytest.fixture
def celery_config():
    """
    Provide Celery configuration for testing.

    Uses eager mode (synchronous execution) by default for fast tests,
    or real worker if TEST_USE_REAL_CELERY=true.
    """
    if Celery is None:
        pytest.skip("Celery not installed")

    return {
        "broker_url": test_settings.celery_broker_url,
        "result_backend": test_settings.celery_result_backend,
        "task_always_eager": not test_settings.use_real_celery,
        "task_eager_propagates": True,
        "task_default_queue": "test",
        "task_default_exchange": "test",
        "task_default_exchange_type": "direct",
        "task_default_routing_key": "test",
    }


@pytest.fixture
def celery_app(celery_config):
    """
    Provide a Celery app instance for testing.

    Configured with eager mode or real worker based on settings.
    """
    if Celery is None:
        pytest.skip("Celery not installed")

    from src.etl.tasks.celery_app import app

    app.conf.update(celery_config)
    return app


# ============================================================================
# File Storage Configuration
# ============================================================================


@pytest.fixture
def temp_fixtures_dir() -> Generator[Path, None, None]:
    """
    Create a temporary fixtures directory for test files.

    Cleaned up automatically after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        fixtures_path = Path(tmpdir)

        # Create subdirectories for test data
        (fixtures_path / "sample_files").mkdir(parents=True, exist_ok=True)

        yield fixtures_path


@pytest.fixture
def temp_upload_dir() -> Generator[Path, None, None]:
    """
    Create a temporary upload directory for test file uploads.

    Cleaned up automatically after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files_dir(temp_fixtures_dir) -> Path:
    """
    Get the path to the sample files directory.

    Returns the temporary fixtures directory with sample files.
    """
    return temp_fixtures_dir / "sample_files"


@pytest.fixture
def mock_responses_dir(temp_fixtures_dir) -> Path:
    """
    Get the path to mock API responses directory.

    Returns the temporary fixtures directory with mock responses.
    """
    return temp_fixtures_dir / "mock_responses"


# ============================================================================
# Sample Media Files - Binary Fixtures
# ============================================================================


@pytest.fixture
def sample_photo_bytes() -> bytes:
    """
    Return minimal valid JPEG bytes for testing photo processors.

    This is a minimal JPEG magic header that's valid for structure testing.
    """
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"


# ============================================================================
# Sample Data Fixtures - Pydantic Models
# ============================================================================


@pytest.fixture
def sample_personality_core():
    """Return a valid PersonalityCore instance for testing."""
    return PersonalityCore(
        openness="High",
        conscientiousness="Medium",
        extraversion="Medium-High",
        agreeableness="Medium",
        emotional_stability="Medium",
        social_match_implications="Compatible with analytical and creative types",
    )


@pytest.fixture
def sample_comfort_zones():
    """Return a valid ComfortZonesAndBoundaries instance."""
    return ComfortZonesAndBoundaries(
        energy_constraints="Prefers one focused meetup rather than multiple plans",
        safety_preferences="Public cafés or coworking spaces",
        time_of_day_comfort="Weekday evenings after 18:00, weekend mornings",
        pace_of_progress="Likes to move from chat to meetup within a few messages",
        topics_to_avoid=["high-conflict political debates", "overly personal topics"],
    )


@pytest.fixture
def sample_social_interaction_style(sample_comfort_zones):
    """Return a valid SocialInteractionStyle instance."""
    return SocialInteractionStyle(
        preferred_group_size="1:1 or small group (2-3 people)",
        meeting_structure="Suggested agenda but open to spontaneity",
        tone="Friendly, slightly technical/analytical with dry humor",
        communication_style="Medium-length messages, occasional emojis",
        response_latency="Typically 2-3 hours in evening",
        conversation_pacing="Steady, focused exchanges leading to concrete plan",
        comfort_zones_and_boundaries=sample_comfort_zones,
    )


@pytest.fixture
def sample_motivations_and_goals():
    """Return a valid MotivationsAndGoals instance."""
    return MotivationsAndGoals(
        primary_goal="Connect with developers/entrepreneurs to build side-projects",
        secondary_goal="Find conversational-Spanish partner for weekend practice",
        underlying_needs=["growth", "relatedness", "autonomy"],
    )


@pytest.fixture
def sample_skills_and_identity():
    """Return a valid SkillsAndIdentity instance."""
    return SkillsAndIdentity(
        skills=["Full-stack developer", "Prototype builder", "Hardware tinkering"],
        skill_levels={
            "Full-stack development": "Advanced",
            "Prototype building": "Advanced",
            "Hardware tinkering": "Intermediate",
        },
        experience="5+ years in software engineering",
        identity_tags=["Developer", "Entrepreneur", "Maker", "Remote worker"],
    )


@pytest.fixture
def sample_availability():
    """Return a valid Availability instance."""
    return Availability(weekday_evenings="after 18:00", weekend_mornings="09:00-12:00")


@pytest.fixture
def sample_mobility():
    """Return a valid Mobility instance."""
    return Mobility(
        preferred_radius_km=5,
        transport_modes=["public transport", "bike", "walk up to 2km"],
    )


@pytest.fixture
def sample_environmental_context():
    """Return a valid EnvironmentalContext instance."""
    return EnvironmentalContext(
        local_area_familiarity="Very familiar with tech-friendly cafés",
        high_density_areas_exposure="Frequently in café-dense areas on weekdays",
    )


@pytest.fixture
def sample_lifestyle_and_rhythms(
    sample_availability, sample_mobility, sample_environmental_context
):
    """Return a valid LifestyleAndRhythms instance."""
    return LifestyleAndRhythms(
        availability=sample_availability,
        weekly_rhythm="Work-focused weekdays, social energy in evenings",
        mobility=sample_mobility,
        preferred_locations=["coworking spaces", "cafés"],
        environmental_context=sample_environmental_context,
    )


@pytest.fixture
def sample_conversation_micro_preferences():
    """Return a valid ConversationMicroPreferences instance."""
    return ConversationMicroPreferences(
        preferred_opener_style="Hey - saw you're into React; fancy a coffee?",
        emoji_usage="light (😊, 👍)",
        humor_style="Dry, self-deprecating maker style",
        formality_level="Informal but respectful - first names",
        preferred_medium="In-app chat with clear time/location",
        default_tone="Calm, friendly, analytical",
    )


@pytest.fixture
def sample_behavioural_history_model():
    """Return a valid BehaviouralHistoryModel instance."""
    return BehaviouralHistoryModel(
        match_acceptance_pattern="Accepts when objective aligns, radius ≤ 2km",
        match_decline_pattern="Declines if distance > 3km or early morning",
        good_outcomes_pattern="Best with shared tech interest + immediate agenda",
        response_latency_pattern="Most responsive early-to-late evenings",
        conversation_patterns="Focused, goal-oriented, aims for specific plan",
    )


@pytest.fixture
def sample_agent_persona_heuristic():
    """Return a valid AgentPersonaHeuristic instance."""
    return AgentPersonaHeuristic(
        voice="Friendly, tech-savvy, proactive but respectful",
        decision_priorities={
            "1": "Shared tech/entrepreneurial interest",
            "2": "Radius ≤ 2km & availability fits",
            "3": "1:1 or small group with clear agenda",
        },
        tone_guidance="Suggest with: 'Here's someone nearby who shares...'",
        risk_tolerance="Medium - values quality over quantity",
        serendipity_openness="High for hobby topics, moderate for social",
    )


# ============================================================================
# Complete UserProfile Fixtures
# ============================================================================


@pytest.fixture
def sample_user_profile_data(
    sample_personality_core,
    sample_social_interaction_style,
    sample_motivations_and_goals,
    sample_skills_and_identity,
    sample_lifestyle_and_rhythms,
    sample_conversation_micro_preferences,
    sample_behavioural_history_model,
    sample_agent_persona_heuristic,
):
    """
    Return a dictionary of valid UserProfile data.

    Useful for API testing where you need dict/JSON format.
    """
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "personality_core": sample_personality_core,
        "social_interaction_style": sample_social_interaction_style,
        "motivations_and_goals": sample_motivations_and_goals,
        "skills_and_identity": sample_skills_and_identity,
        "lifestyle_and_rhythms": sample_lifestyle_and_rhythms,
        "conversation_micro_preferences": sample_conversation_micro_preferences,
        "behavioural_history_model": sample_behavioural_history_model,
        "agent_persona_heuristic": sample_agent_persona_heuristic,
        "is_active": True,
    }


@pytest.fixture
def sample_user_profile(sample_user_profile_data):
    """
    Return a complete UserProfile instance.

    This is a full, valid profile ready for database insertion.
    """
    return UserProfile(**sample_user_profile_data)


@pytest.fixture
def saved_user_profile(db_session, sample_user_profile):
    """
    Return a UserProfile that has been saved to the database.

    Use this when you need a profile that already exists in the database
    with an ID and timestamps.
    """
    db_session.add(sample_user_profile)
    db_session.commit()
    db_session.refresh(sample_user_profile)
    return sample_user_profile


# ============================================================================
# Factory Fixtures (for generating multiple instances)
# ============================================================================


@pytest.fixture
def profile_factory(db_session):
    """
    Return a factory function for creating multiple profiles.

    Usage:
        profile1 = profile_factory(user_id="550e8400-e29b-41d4-a716-446655440001")
        profile2 = profile_factory(user_id="550e8400-e29b-41d4-a716-446655440002")
    """

    def _create_profile(user_id=None, **overrides):
        """Create a profile with default or custom values."""
        if user_id is None:
            from circles.src.utils.uuid_utils import generate_user_id

            user_id = generate_user_id()

        # Create default nested models
        default_data = {
            "user_id": user_id,
            "personality_core": PersonalityCore(
                openness="Medium",
                conscientiousness="Medium",
                extraversion="Medium",
                agreeableness="Medium",
                emotional_stability="Medium",
                social_match_implications="Test user",
            ),
            "social_interaction_style": SocialInteractionStyle(
                preferred_group_size="Flexible",
                meeting_structure="Flexible",
                tone="Casual",
                communication_style="Brief",
                response_latency="Variable",
                conversation_pacing="Flexible",
                comfort_zones_and_boundaries=ComfortZonesAndBoundaries(
                    energy_constraints="Medium",
                    safety_preferences="Standard",
                    time_of_day_comfort="Flexible",
                    pace_of_progress="Medium",
                    topics_to_avoid=[],
                ),
            ),
            "motivations_and_goals": MotivationsAndGoals(
                primary_goal="Test goal",
                secondary_goal="Test secondary",
                underlying_needs=["test"],
            ),
            "skills_and_identity": SkillsAndIdentity(
                skills=["General"],
                skill_levels={"General": "Beginner"},
                experience="Minimal",
                identity_tags=["User"],
            ),
            "lifestyle_and_rhythms": LifestyleAndRhythms(
                availability=Availability(
                    weekday_evenings="Flexible", weekend_mornings="Flexible"
                ),
                weekly_rhythm="Standard",
                mobility=Mobility(preferred_radius_km=10, transport_modes=["Any"]),
                preferred_locations=["Anywhere"],
                environmental_context=EnvironmentalContext(
                    local_area_familiarity="Medium",
                    high_density_areas_exposure="Medium",
                ),
            ),
            "conversation_micro_preferences": ConversationMicroPreferences(
                preferred_opener_style="Standard",
                emoji_usage="Medium",
                humor_style="Neutral",
                formality_level="Medium",
                preferred_medium="Any",
                default_tone="Neutral",
            ),
            "behavioural_history_model": BehaviouralHistoryModel(
                match_acceptance_pattern="Standard",
                match_decline_pattern="Standard",
                good_outcomes_pattern="Standard",
                response_latency_pattern="Standard",
                conversation_patterns="Standard",
            ),
            "agent_persona_heuristic": AgentPersonaHeuristic(
                voice="Standard",
                decision_priorities={"1": "Standard"},
                tone_guidance="Standard",
                risk_tolerance="Medium",
                serendipity_openness="Medium",
            ),
            "is_active": True,
        }

        # Apply overrides
        default_data.update(overrides)

        profile = UserProfile(**default_data)
        return profile

    return _create_profile


# ============================================================================
# ETL Data Type Factories
# ============================================================================


@pytest.fixture
def sample_photo_bytes() -> bytes:
    """
    Provide sample photo data as bytes (minimal PNG).

    This is a very small valid PNG file (8x8 transparent).
    """
    # Minimal 8x8 transparent PNG (89 bytes)
    return bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,
            0x00,
            0x00,
            0x00,
            0x0D,
            0x49,
            0x48,
            0x44,
            0x52,
            0x00,
            0x00,
            0x00,
            0x08,
            0x00,
            0x00,
            0x00,
            0x08,
            0x08,
            0x06,
            0x00,
            0x00,
            0x00,
            0xC4,
            0x0F,
            0xBE,
            0x8B,
            0x00,
            0x00,
            0x00,
            0x19,
            0x74,
            0x45,
            0x58,
            0x74,
            0x53,
            0x6F,
            0x66,
            0x74,
            0x77,
            0x61,
            0x72,
            0x65,
            0x00,
            0x41,
            0x64,
            0x6F,
            0x62,
            0x65,
            0x20,
            0x49,
            0x6D,
            0x61,
            0x67,
            0x65,
            0x52,
            0x65,
            0x61,
            0x64,
            0x79,
            0x71,
            0xC9,
            0x65,
            0x3C,
            0x00,
            0x00,
            0x00,
            0x1A,
            0x49,
            0x44,
            0x41,
            0x54,
            0x78,
            0x9A,
            0x62,
            0xF8,
            0x0F,
            0x00,
            0x00,
            0x01,
            0x01,
            0x01,
            0x00,
            0x18,
            0xDD,
            0x8D,
            0xB4,
            0x00,
            0x00,
            0x00,
            0x00,
            0x49,
            0x45,
            0x4E,
            0x44,
            0xAE,
            0x42,
            0x60,
            0x82,
        ]
    )


@pytest.fixture
def sample_audio_bytes() -> bytes:
    """
    Provide sample audio data as bytes (minimal WAV).

    This is a minimal valid WAV file (1 second, 44100 Hz, mono).
    """
    # Minimal WAV header (1 second silence at 44100 Hz)
    import io
    import wave

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(44100)
        wav_file.writeframes(b"\x00\x00" * 44100)  # 1 second of silence

    return wav_buffer.getvalue()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """
    Provide sample PDF data as bytes (minimal PDF).

    This is a very minimal valid PDF file.
    """
    # Minimal PDF header and structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
217
%%EOF
"""


@pytest.fixture
def sample_csv_data() -> str:
    """
    Provide sample CSV data for calendar/email fixtures.

    Returns CSV formatted text data.
    """
    return """date,time,title,description
2024-01-15,10:00,Meeting 1,Team sync
2024-01-15,14:30,Meeting 2,Project review
2024-01-16,09:00,Meeting 3,Client call
2024-01-16,16:00,Meeting 4,1-on-1
"""


@pytest.fixture
def sample_json_data() -> dict:
    """
    Provide sample JSON data for various fixtures.

    Returns a dictionary representing typical structured data.
    """
    return {
        "id": "sample_001",
        "type": "test",
        "title": "Sample Data",
        "content": "This is test content",
        "metadata": {
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "tags": ["test", "sample"],
        },
    }


# ============================================================================
# Cleanup and Utility Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_database_state(db_session):
    """
    Automatically reset database state after each test.

    This is a safety fixture that ensures complete cleanup even if
    a test doesn't properly clean up after itself.
    """
    yield
    # Cleanup happens automatically via db_session fixture rollback


@pytest.fixture
def freeze_time():
    """
    Fixture for freezing time during tests (if needed).

    Requires freezegun: pip install freezegun
    """
    try:
        from freezegun import freeze_time

        return freeze_time
    except ImportError:
        pytest.skip("freezegun not installed")


# ============================================================================
# Marker Configuration
# ============================================================================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests that don't require database")
    config.addinivalue_line(
        "markers", "integration: Integration tests that require database"
    )
    config.addinivalue_line("markers", "slow: Slow-running tests (> 1 second)")
    config.addinivalue_line("markers", "api: API endpoint tests (requires FastAPI)")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


# ============================================================================
# Test Collection Hooks
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.

    This hook automatically adds markers to tests based on their location:
    - tests/unit/ -> @pytest.mark.unit
    - tests/integration/ -> @pytest.mark.integration
    - tests/e2e/ -> @pytest.mark.e2e
    """
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
