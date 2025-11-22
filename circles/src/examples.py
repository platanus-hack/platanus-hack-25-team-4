"""
Example usage of the UserProfile SQLModel.

This module demonstrates how to create, read, update, and query user profiles
using SQLModel with the database.
"""

from datetime import datetime

from sqlmodel import Session, select

from circles.src.database import SessionLocal, create_db_and_tables, engine
from circles.src.profile_schema import (
    AgentPersonaHeuristic,
    Availability,
    BehaviouralHistoryModel,
    ComfortZonesAndBoundaries,
    ConversationMicroPreferences,
    EnvironmentalContext,
    Interest,
    LifestyleAndRhythms,
    Mobility,
    MotivationsAndGoals,
    PersonalityCore,
    SkillsAndIdentity,
    SocialInteractionStyle,
    UserProfile,
)


def create_example_profile() -> UserProfile:
    """Create an example user profile based on the profile.example.json."""

    personality_core = PersonalityCore(
        openness="High",
        conscientiousness="High",
        extraversion="Medium-High",
        agreeableness="Medium",
        emotional_stability="Medium",
        social_match_implications="High openness and medium-high extraversion mean they enjoy meeting new people around shared projects and ideas, while high conscientiousness makes them reliable about showing up when a plan is clear. Medium agreeableness and emotional stability mean they prefer low-drama, practical interactions with respectful but direct communication and clear expectations about time and place.",
    )

    comfort_zones = ComfortZonesAndBoundaries(
        energy_constraints="After work, prefers one focused 1:1 or very small-group meetup rather than multiple back-to-back plans; social battery is lower on weekday mornings.",
        safety_preferences="Prefers to meet in public, well-known cafés or coworking spaces; comfortable with mixed-gender groups but not with very large or noisy parties for first meetings.",
        time_of_day_comfort="Most comfortable with weekday evenings after 18:00 and weekend mornings; avoids very early weekday mornings and late Sunday nights.",
        pace_of_progress="Likes to move from chat to a concrete low-pressure meetup within a few messages if the match looks good, rather than weeks of back-and-forth.",
        topics_to_avoid=[
            "high-conflict political debates in first meetings",
            "overly personal or dramatic topics before basic rapport is built",
        ],
    )

    social_interaction_style = SocialInteractionStyle(
        preferred_group_size="1:1 or very small group (2-3 people)",
        meeting_structure="prefers a suggested agenda but open to spontaneity",
        tone="friendly, slightly technical/analytical with a bit of dry humor",
        communication_style="medium-length messages, occasional emojis (😊, 👍), casual first-name basis",
        response_latency="typically within ~2-3 hours in the evening, slower after midnight",
        conversation_pacing="Responds at a steady but not hyper-instant pace; prefers a few focused exchanges leading to a concrete plan over long small-talk threads.",
        comfort_zones_and_boundaries=comfort_zones,
    )

    motivations_and_goals = MotivationsAndGoals(
        primary_goal="Connect with fellow developers/entrepreneurs in Santiago to build side-projects and share ideas.",
        secondary_goal="Find a regular conversational-Spanish partner to practice and improve fluency on weekend mornings.",
        underlying_needs=[
            "growth (learning & creation)",
            "relatedness (meeting like-minded people locally)",
            "autonomy (choosing his own path)",
        ],
    )

    skills_and_identity = SkillsAndIdentity(
        skills=[
            "Full-stack developer (React / Node.js)",
            "Prototype app builder",
            "Hobbyist with Raspberry Pi/hardware projects",
        ],
        skill_levels={
            "Full-stack development (React / Node.js)": "Advanced",
            "Prototype app building": "Advanced",
            "Hardware tinkering / Raspberry Pi": "Intermediate",
        },
        experience="5+ years in software engineering; one small startup project; active GitHub contributor",
        identity_tags=[
            "Developer",
            "Entrepreneur",
            "Maker",
            "Chile-resident (Santiago)",
            "Spanish native / English fluent",
            "Remote worker",
            "Expat",
        ],
    )

    availability = Availability(
        weekday_evenings="after 18:00", weekend_mornings="09:00-12:00"
    )

    mobility = Mobility(
        preferred_radius_km=2,
        transport_modes=["public transport", "bike", "comfortable walking up to ~2 km"],
    )

    environmental_context = EnvironmentalContext(
        local_area_familiarity="Very familiar with Las Condes and Providencia, especially tech-friendly cafés and coworking spaces.",
        high_density_areas_exposure="Frequently works from or passes through café-dense areas on weekdays, making short-notice evening meetups feasible within a 1–2 km radius.",
    )

    lifestyle_and_rhythms = LifestyleAndRhythms(
        availability=availability,
        weekly_rhythm="Work-focused during weekdays with social and side-project energy mainly concentrated in weekday evenings; reserves weekend mornings for language practice or relaxed coffee meetups.",
        mobility=mobility,
        preferred_locations=[
            "coworking spaces",
            "cafés in Las Condes/Providencia, Santiago",
        ],
        environmental_context=environmental_context,
    )

    conversation_micro_preferences = ConversationMicroPreferences(
        preferred_opener_style="Hey — saw you're into React and hardware; fancy a coffee and code-chat this weekend?",
        emoji_usage="light (😊, 🙂, 👍)",
        humor_style='dry, self-deprecating hobby-maker style ("Yes, the Raspberry Pi project is still in the drawer").',
        formality_level="informal but respectful — first names used",
        preferred_medium="in-app chat; comfortable with short suggestion + time/location rather than long debate",
        default_tone="calm, friendly, and slightly analytical — focuses on practical details and shared interests rather than high-intensity hype.",
    )

    behavioural_history_model = BehaviouralHistoryModel(
        match_acceptance_pattern="Accepts matches where objective closely aligns (tech/entrepreneurial), radius ≤ 2 km, clear time + place.",
        match_decline_pattern="Declines matches if distance > ~3 km or if time window is early morning on a weekday.",
        good_outcomes_pattern='Best outcomes when meeting someone with shared tech interest + immediate agenda (e.g., coffee + brainstorm rather than vague "let\'s meet").',
        response_latency_pattern="Most responsive in early-to-late evenings; replies may be delayed to the next day if messages arrive very late at night or during deep-focus work blocks.",
        conversation_patterns="Tends to keep pre-meetup chats focused and goal-oriented, aiming to converge on a specific time and place within a handful of messages rather than long exploratory conversations.",
    )

    agent_persona_heuristic = AgentPersonaHeuristic(
        voice="Friendly, tech-savvy, proactive but respectful of time.",
        decision_priorities={
            "1": "Shared tech/entrepreneurial interest → high priority",
            "2": "Radius ≤ 2 km & availability fits evening/weekend windows",
            "3": "Match type fits 1:1 or small group, clear agenda",
            "4": "Avoid matches >3 km or time windows outside preferred rhythm",
        },
        tone_guidance='Suggest matches with: "Here\'s someone nearby who shares your developer background and is free this Thursday evening – want me to introduce?"',
        risk_tolerance="Medium – open to new people but sensitive to wasted time; values quality over quantity.",
        serendipity_openness='High for hobby/hardware topics; moderate for purely social "hang out" invites.',
    )

    # Create interests
    interests = [
        Interest(
            title="Trabajo",
            description="Busco / Ofrezco trabajo, soy dev y busco startups",
        ),
        Interest(
            title="Side Projects",
            description="Building prototypes and apps with React and Node.js",
        ),
        Interest(
            title="Hardware",
            description="Hobbyist projects with Raspberry Pi and electronics",
        ),
        Interest(
            title="Spanish Learning",
            description="Practicing conversational Spanish on weekend mornings",
        ),
    ]

    # Create the profile
    profile = UserProfile(
        user_id="user_santiago_001",
        bio="Full-stack developer in Santiago interested in startups, side projects, and hardware tinkering.",
        interests=interests,
        profile_completed=True,
        personality_core=personality_core,
        social_interaction_style=social_interaction_style,
        motivations_and_goals=motivations_and_goals,
        skills_and_identity=skills_and_identity,
        lifestyle_and_rhythms=lifestyle_and_rhythms,
        conversation_micro_preferences=conversation_micro_preferences,
        behavioural_history_model=behavioural_history_model,
        agent_persona_heuristic=agent_persona_heuristic,
        is_active=True,
    )

    return profile


def insert_example_profile():
    """Insert example profile into database."""
    create_db_and_tables()

    with SessionLocal() as session:
        profile = create_example_profile()
        session.add(profile)
        session.commit()
        session.refresh(profile)
        print(f"Created profile with ID: {profile.id}, User ID: {profile.user_id}")
        return profile


def query_profiles_by_user_id(user_id: str):
    """Query a profile by user_id."""
    with SessionLocal() as session:
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        profile = session.exec(statement).first()
        if profile:
            print(f"Found profile: {profile.user_id}")
            print(f"Primary goal: {profile.motivations_and_goals.primary_goal}")
        return profile


def query_active_profiles():
    """Query all active profiles."""
    with SessionLocal() as session:
        statement = select(UserProfile).where(UserProfile.is_active == True)
        profiles = session.exec(statement).all()
        print(f"Found {len(profiles)} active profiles")
        return profiles


def update_profile_last_matched(user_id: str, last_matched: datetime):
    """Update a profile's last_matched timestamp."""
    with SessionLocal() as session:
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        profile = session.exec(statement).first()

        if profile:
            profile.last_matched = last_matched
            profile.updated_at = datetime.utcnow()
            session.add(profile)
            session.commit()
            session.refresh(profile)
            print(f"Updated {user_id} last_matched to {last_matched}")


if __name__ == "__main__":
    # Example usage
    print("Creating example profile...")
    insert_example_profile()

    print("\nQuerying profile...")
    query_profiles_by_user_id("user_santiago_001")

    print("\nQuerying all active profiles...")
    query_active_profiles()
