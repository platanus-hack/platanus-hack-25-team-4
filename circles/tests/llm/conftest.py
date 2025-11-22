"""LLM-specific test fixtures and mocks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI AsyncOpenAI client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Setup response chain
    mock_message.content = "This is a test response from OpenAI"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    # Setup client methods
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_client.close = AsyncMock()

    with patch("src.etl.adapters.llm.openai_adapter.AsyncOpenAI") as mock_class:
        mock_class.return_value = mock_client
        yield {"class": mock_class, "client": mock_client, "response": mock_response}


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic AsyncAnthropic client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_content = MagicMock()

    # Setup response chain
    mock_content.text = "This is a test response from Anthropic"
    mock_response.content = [mock_content]

    # Setup client methods
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    mock_client.close = AsyncMock()

    with patch("src.etl.adapters.llm.anthropic_adapter.AsyncAnthropic") as mock_class:
        mock_class.return_value = mock_client
        yield {"class": mock_class, "client": mock_client, "response": mock_response}


@pytest.fixture
def openai_config():
    """Default OpenAI config for testing."""
    from src.etl.adapters.llm import OpenAIConfig

    return OpenAIConfig(
        api_key="test-openai-key", model="gpt-4", max_tokens=100, temperature=0.7
    )


@pytest.fixture
def anthropic_config():
    """Default Anthropic config for testing."""
    from src.etl.adapters.llm import AnthropicConfig

    return AnthropicConfig(
        api_key="test-anthropic-key",
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        temperature=0.7,
    )


@pytest.fixture
async def mock_openai_adapter(openai_config, mock_openai_client):
    """Fully mocked OpenAI adapter ready for testing."""
    from src.etl.adapters.llm import OpenAIAdapter

    adapter = OpenAIAdapter(openai_config)
    adapter._client = mock_openai_client["client"]

    yield adapter

    await adapter.close()


@pytest.fixture
async def mock_anthropic_adapter(anthropic_config, mock_anthropic_client):
    """Fully mocked Anthropic adapter ready for testing."""
    from src.etl.adapters.llm import AnthropicAdapter

    adapter = AnthropicAdapter(anthropic_config)
    adapter._client = mock_anthropic_client["client"]

    yield adapter

    await adapter.close()
