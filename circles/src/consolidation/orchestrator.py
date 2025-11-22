"""
Profile Consolidation Orchestrator - Coordinates the consolidation pipeline.

Manages data aggregation, strategy selection (via dependency injection),
LLM provider selection, and profile persistence.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..etl.core.result import Result
from ..profile_schema import UserProfile
from .data_aggregator import DataAggregator
from .llm_adapter import LLMProvider, LLMProviderFactory
from .strategy import ConsolidationStrategy, DefaultConsolidationStrategy

logger = logging.getLogger(__name__)


class ProfileConsolidationOrchestrator:
    """
    Orchestrates the profile consolidation pipeline.

    Coordinates:
    - Data aggregation from multiple sources
    - Strategy selection and execution (via dependency injection)
    - LLM provider selection (via dependency injection)
    - Profile persistence to database
    """

    def __init__(
        self,
        session: AsyncSession,
        strategy: Optional[ConsolidationStrategy] = None,
        llm_provider: Optional[LLMProvider] = None,
        llm_provider_name: str = "anthropic",
    ):
        """
        Initialize orchestrator with database session and injected dependencies.

        Args:
            session: AsyncSession for database operations
            strategy: Optional injected ConsolidationStrategy instance (defaults to DefaultConsolidationStrategy)
            llm_provider: Optional injected LLMProvider instance
            llm_provider_name: LLM provider name ('anthropic' or 'openai') if llm_provider not provided
        """
        self.session = session
        self.strategy = strategy
        self.llm_provider = llm_provider
        self.llm_provider_name = llm_provider_name
        self.aggregator = DataAggregator(session)

    async def consolidate_user_profile(
        self,
        user_id: int,
    ) -> Result[UserProfile, Exception]:
        """
        Consolidate a user profile from all available data sources.

        Pipeline:
        1. Aggregate all user data from multiple sources
        2. Get or create LLM provider
        3. Get or create consolidation strategy
        4. Call consolidation strategy with injected LLM provider
        5. Persist consolidated profile to database
        6. Return result

        Args:
            user_id: The user ID to consolidate

        Returns:
            Result[UserProfile, Exception]: Consolidated profile or error
        """
        try:
            logger.info(f"Starting profile consolidation for user: {user_id}")

            # Step 1: Aggregate user data
            data_result = await self.aggregator.aggregate_user_data(user_id)
            if data_result.is_error:
                logger.error(f"Failed to aggregate data for user {user_id}")
                return Result.error(data_result.error_value)

            raw_data = data_result.value

            # Step 2: Get or create LLM provider
            llm_provider = self._get_llm_provider()

            # Step 3: Get or create consolidation strategy
            strategy = self._get_strategy(user_id)

            # Step 4: Call consolidation strategy with injected LLM provider
            profile_result = await strategy.consolidate(user_id, raw_data, llm_provider)
            if profile_result.is_error:
                logger.error(f"Consolidation strategy failed for user {user_id}")
                return Result.error(profile_result.error_value)

            profile = profile_result.value

            # Step 5: Persist profile to database
            persist_result = await self._persist_profile(profile)
            if persist_result.is_error:
                logger.error(f"Failed to persist profile for user {user_id}")
                return Result.error(persist_result.error_value)

            logger.info(f"Successfully consolidated profile for user {user_id}")
            return Result.ok(profile)

        except Exception as e:
            logger.error(
                f"Unexpected error in consolidation pipeline for user {user_id}: {e}"
            )
            return Result.error(e)

    def _get_llm_provider(self) -> LLMProvider:
        """
        Get LLM provider - either injected or create based on provider name.

        Returns:
            LLMProvider instance
        """
        if self.llm_provider:
            return self.llm_provider

        # Create provider based on name
        return LLMProviderFactory.create(self.llm_provider_name)

    def _get_strategy(self, user_id: int) -> ConsolidationStrategy:
        """
        Get consolidation strategy - either injected or default.

        Args:
            user_id: User ID for strategy initialization

        Returns:
            ConsolidationStrategy instance
        """
        if self.strategy:
            return self.strategy

        # Default to DefaultConsolidationStrategy
        return DefaultConsolidationStrategy(user_id)

    async def _persist_profile(
        self, profile: UserProfile
    ) -> Result[UserProfile, Exception]:
        """
        Persist consolidated profile to database.

        Args:
            profile: UserProfile to persist

        Returns:
            Result[UserProfile, Exception]: Persisted profile or error
        """
        try:
            self.session.add(profile)
            await self.session.commit()
            await self.session.refresh(profile)

            logger.debug(f"Persisted profile for user {profile.user_id}")
            return Result.ok(profile)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error persisting profile: {e}")
            return Result.error(e)

    @staticmethod
    def create_with_dependencies(
        session: AsyncSession,
        strategy: Optional[ConsolidationStrategy] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> "ProfileConsolidationOrchestrator":
        """
        Create orchestrator with explicitly injected dependencies.

        This factory method enables full dependency injection.

        Args:
            session: AsyncSession for database operations
            strategy: Optional injected ConsolidationStrategy (defaults to DefaultConsolidationStrategy)
            llm_provider: Optional injected LLMProvider (defaults to Anthropic)

        Returns:
            ProfileConsolidationOrchestrator with injected dependencies
        """
        return ProfileConsolidationOrchestrator(
            session=session,
            strategy=strategy,
            llm_provider=llm_provider,
        )

    @staticmethod
    def create_with_llm_provider(
        session: AsyncSession,
        llm_provider_name: str = "anthropic",
    ) -> "ProfileConsolidationOrchestrator":
        """
        Create orchestrator with LLM provider selection.

        Args:
            session: AsyncSession for database operations
            llm_provider_name: LLM provider name ('anthropic' or 'openai')

        Returns:
            ProfileConsolidationOrchestrator with selected LLM provider
        """
        return ProfileConsolidationOrchestrator(
            session=session,
            llm_provider_name=llm_provider_name,
        )

    @staticmethod
    def create_with_strategy(
        session: AsyncSession,
        strategy: ConsolidationStrategy,
        llm_provider: Optional[LLMProvider] = None,
    ) -> "ProfileConsolidationOrchestrator":
        """
        Create orchestrator with explicitly injected strategy.

        This factory method enables custom consolidation strategies to be injected,
        supporting advanced use cases where default LLM-based consolidation is
        replaced with domain-specific logic.

        Args:
            session: AsyncSession for database operations
            strategy: Injected ConsolidationStrategy instance
            llm_provider: Optional injected LLMProvider (defaults to Anthropic if None)

        Returns:
            ProfileConsolidationOrchestrator configured with injected strategy

        Example:
            >>> custom_strategy = MyCustomStrategy()
            >>> orchestrator = ProfileConsolidationOrchestrator.create_with_strategy(
            ...     session=db_session,
            ...     strategy=custom_strategy
            ... )
        """
        return ProfileConsolidationOrchestrator(
            session=session,
            strategy=strategy,
            llm_provider=llm_provider,
        )
