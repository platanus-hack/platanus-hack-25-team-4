"""
Consolidation Celery Tasks - Background task queue for profile consolidation.

Executes the profile consolidation pipeline asynchronously when triggered.
Allows the API to respond quickly while consolidation happens in the background.
"""

import asyncio
import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ...consolidation.orchestrator import ProfileConsolidationOrchestrator
from ..core import get_settings
from .celery_app import celery_app

logger = logging.getLogger(__name__)

# Database engine (singleton pattern)
_engine = None
_async_session_factory = None


async def init_db_engine():
    """Initialize database engine and session factory."""
    global _engine, _async_session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
        )
        _async_session_factory = sessionmaker(
            _engine, class_=AsyncSession, expire_on_delete=False
        )
    return _async_session_factory


async def get_db_session():
    """Get database session."""
    factory = await init_db_engine()
    async with factory() as session:
        yield session


async def _run_async_consolidation(
    user_id: str,
    llm_provider_name: str = "anthropic",
) -> Dict[str, Any]:
    """
    Run async consolidation pipeline.

    Args:
        user_id: The user ID to consolidate
        llm_provider_name: LLM provider to use ('anthropic' or 'openai')

    Returns:
        Result dictionary with status and profile data
    """
    try:
        # Initialize database
        factory = await init_db_engine()

        async with factory() as session:
            # Create orchestrator with LLM provider
            orchestrator = ProfileConsolidationOrchestrator.create_with_llm_provider(
                session, llm_provider_name=llm_provider_name
            )

            # Execute consolidation
            result = await orchestrator.consolidate_user_profile(user_id)

            if result.is_ok:
                profile = result.value
                return {
                    "status": "success",
                    "user_id": user_id,
                    "profile_id": profile.id,
                    "message": f"Profile consolidated successfully for user {user_id}",
                }
            else:
                error = result.error_value
                logger.error(f"Consolidation failed for user {user_id}: {error}")
                return {
                    "status": "failed",
                    "user_id": user_id,
                    "error": str(error),
                    "message": f"Profile consolidation failed for user {user_id}",
                }

    except Exception as e:
        logger.error(f"Unexpected error during consolidation for user {user_id}: {e}")
        return {
            "status": "error",
            "user_id": user_id,
            "error": str(e),
            "message": f"Unexpected error during consolidation for user {user_id}",
        }


@celery_app.task(
    name="consolidate_user_profile",
    bind=True,
    max_retries=3,
    time_limit=600,  # 10 minutes
)
def consolidate_user_profile_task(
    self,
    user_id: str,
    llm_provider_name: str = "anthropic",
) -> Dict[str, Any]:
    """
    Celery task to consolidate user profile.

    Args:
        self: Celery task instance
        user_id: The user ID to consolidate
        llm_provider_name: LLM provider to use ('anthropic' or 'openai')

    Returns:
        Result dictionary with consolidation status

    Raises:
        Retries task on failure (up to max_retries times)
    """
    try:
        logger.info(
            f"Starting profile consolidation for user: {user_id} with provider: {llm_provider_name}"
        )

        # Run async consolidation in synchronous Celery context
        result = asyncio.run(_run_async_consolidation(user_id, llm_provider_name))

        if result["status"] == "success":
            logger.info(f"Successfully consolidated profile for user {user_id}")
        else:
            logger.warning(
                f"Consolidation task returned status: {result['status']} for user {user_id}"
            )

        return result

    except Exception as exc:
        logger.error(f"Error consolidating profile for user {user_id}: {exc}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for consolidation of user {user_id}")
            return {
                "status": "error",
                "user_id": user_id,
                "error": str(exc),
                "message": f"Profile consolidation failed after max retries for user {user_id}",
            }


@celery_app.task(
    name="consolidate_user_profile_with_strategy",
    bind=True,
    max_retries=3,
    time_limit=600,  # 10 minutes
)
def consolidate_user_profile_with_strategy_task(
    self,
    user_id: str,
    strategy_class_name: str,
) -> Dict[str, Any]:
    """
    Celery task to consolidate user profile with custom strategy.

    This task enables dependency injection of custom consolidation strategies.

    Args:
        self: Celery task instance
        user_id: The user ID to consolidate
        strategy_class_name: Fully qualified class name of ConsolidationStrategy

    Returns:
        Result dictionary with consolidation status

    Raises:
        Retries task on failure (up to max_retries times)
    """
    try:
        logger.info(
            f"Starting profile consolidation for user: {user_id} with custom strategy: {strategy_class_name}"
        )

        # Import and instantiate strategy dynamically
        module_name, class_name = strategy_class_name.rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        StrategyClass = getattr(module, class_name)

        # Create strategy instance
        strategy = StrategyClass(user_id)

        # Run async consolidation with injected strategy
        async def _run_with_strategy():
            factory = await init_db_engine()
            async with factory() as session:
                orchestrator = ProfileConsolidationOrchestrator.create_with_strategy(
                    session, strategy=strategy
                )
                result = await orchestrator.consolidate_user_profile(user_id)

                if result.is_ok:
                    profile = result.value
                    return {
                        "status": "success",
                        "user_id": user_id,
                        "profile_id": profile.id,
                        "message": f"Profile consolidated successfully for user {user_id}",
                    }
                else:
                    error = result.error_value
                    return {
                        "status": "failed",
                        "user_id": user_id,
                        "error": str(error),
                    }

        result = asyncio.run(_run_with_strategy())

        if result["status"] == "success":
            logger.info(
                f"Successfully consolidated profile for user {user_id} with custom strategy"
            )
        else:
            logger.warning(
                f"Consolidation with custom strategy returned status: {result['status']}"
            )

        return result

    except Exception as exc:
        logger.error(
            f"Error in custom strategy consolidation for user {user_id}: {exc}"
        )

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Max retries exceeded for custom strategy consolidation of user {user_id}"
            )
            return {
                "status": "error",
                "user_id": user_id,
                "error": str(exc),
            }
