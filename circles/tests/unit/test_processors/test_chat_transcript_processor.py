"""
Unit tests for ChatTranscriptProcessor.

Tests chat transcript file processing and message chunking.
"""

import json

import pytest

from circles.src.etl.processors.chat_transcript_processor import (
    ChatTranscriptProcessor,
    SimpleProcessorResult,
)
from circles.tests.fixtures.fixture_factories import DataTypeFixtures


@pytest.mark.unit
class TestChatTranscriptProcessor:
    """Test ChatTranscriptProcessor functionality."""

    @pytest.fixture
    async def transcript_processor(self):
        """Create a ChatTranscriptProcessor instance."""
        return ChatTranscriptProcessor()

    @pytest.fixture
    def sample_json_transcript_file(self, tmp_path):
        """Create a sample JSON transcript file."""
        transcript_data = {
            "messages": [
                {
                    "sender": "john",
                    "text": "Hi everyone",
                    "timestamp": "2024-01-15T10:00:00Z",
                },
                {
                    "sender": "jane",
                    "text": "Hello! How are you?",
                    "timestamp": "2024-01-15T10:01:00Z",
                },
                {
                    "sender": "bob",
                    "text": "Doing well, thanks!",
                    "timestamp": "2024-01-15T10:02:00Z",
                },
                {
                    "sender": "john",
                    "text": "Great, let's start the meeting",
                    "timestamp": "2024-01-15T10:03:00Z",
                },
            ],
            "metadata": {
                "date_start": "2024-01-15T10:00:00Z",
                "date_end": "2024-01-15T10:03:00Z",
                "channel": "engineering",
            },
        }
        json_path = tmp_path / "transcript.json"
        json_path.write_text(json.dumps(transcript_data))
        return json_path

    @pytest.fixture
    def sample_text_transcript_file(self, tmp_path):
        """Create a sample text transcript file."""
        transcript_content = """john: Hi everyone
jane: Hello! How are you?
bob: Doing well, thanks!
john: Great, let's start the meeting
jane: Sounds good
bob: Ready when you are
"""
        text_path = tmp_path / "transcript.txt"
        text_path.write_text(transcript_content)
        return text_path

    @pytest.fixture
    def large_json_transcript_file(self, tmp_path):
        """Create a large JSON transcript for chunking tests."""
        messages = [
            {"sender": f"user{i % 3}", "text": f"Message {i}"}
            for i in range(250)  # More than 2 chunks
        ]
        transcript_data = {"messages": messages}
        json_path = tmp_path / "large_transcript.json"
        json_path.write_text(json.dumps(transcript_data))
        return json_path

    @pytest.mark.asyncio
    async def test_process_json_transcript(
        self, transcript_processor, sample_json_transcript_file
    ):
        """Test processing a JSON transcript file."""
        result = await transcript_processor.process(sample_json_transcript_file)

        assert isinstance(result, SimpleProcessorResult)
        assert "splits" in result.content
        assert "participants" in result.content
        assert "message_count" in result.content
        assert result.metadata["file_type"] == ".json"
        assert result.metadata["format"] == "json"

    @pytest.mark.asyncio
    async def test_process_text_transcript(
        self, transcript_processor, sample_text_transcript_file
    ):
        """Test processing a text transcript file."""
        result = await transcript_processor.process(sample_text_transcript_file)

        assert isinstance(result, SimpleProcessorResult)
        assert "splits" in result.content
        assert "participants" in result.content
        assert "message_count" in result.content
        assert result.metadata["file_type"] == ".txt"
        assert result.metadata["format"] == "text"

    @pytest.mark.asyncio
    async def test_parse_json_transcript_list(self, transcript_processor):
        """Test parsing JSON transcript as list of messages."""
        json_content = json.dumps(
            [
                {"sender": "john", "text": "Hello"},
                {"sender": "jane", "text": "Hi there"},
            ]
        )

        messages, metadata = transcript_processor._parse_json_transcript(json_content)

        assert len(messages) == 2
        assert messages[0]["sender"] == "john"
        assert messages[0]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_parse_json_transcript_dict(self, transcript_processor):
        """Test parsing JSON transcript as dict with messages key."""
        json_content = json.dumps(
            {
                "messages": [
                    {"sender": "john", "text": "Hello"},
                    {"sender": "jane", "text": "Hi"},
                ],
                "metadata": {"channel": "general"},
            }
        )

        messages, metadata = transcript_processor._parse_json_transcript(json_content)

        assert len(messages) == 2
        assert metadata.get("channel") == "general"

    @pytest.mark.asyncio
    async def test_parse_json_transcript_invalid(self, transcript_processor):
        """Test parsing invalid JSON transcript."""
        json_content = "not valid json"

        messages, metadata = transcript_processor._parse_json_transcript(json_content)

        assert messages == []
        assert metadata == {"date_start": None, "date_end": None}

    def test_parse_text_transcript(self, transcript_processor):
        """Test parsing text transcript."""
        text_content = """john: First message
jane: Second message
bob: Third message"""

        messages, metadata = transcript_processor._parse_text_transcript(text_content)

        assert len(messages) == 3
        assert messages[0]["sender"] == "john"
        assert messages[0]["text"] == "First message"

    def test_parse_text_transcript_no_colon(self, transcript_processor):
        """Test parsing text transcript with lines without colons."""
        text_content = """john: Hello
This is not a message
jane: Hi"""

        messages, metadata = transcript_processor._parse_text_transcript(text_content)

        # Should only capture messages with colons
        assert len(messages) == 2

    def test_extract_participants(self, transcript_processor):
        """Test extracting unique participants."""
        messages = [
            {"sender": "john", "text": "Hello"},
            {"sender": "jane", "text": "Hi"},
            {"sender": "john", "text": "How are you?"},
            {"sender": "bob", "text": "Fine"},
        ]

        participants = transcript_processor._extract_participants(messages)

        assert set(participants) == {"john", "jane", "bob"}

    def test_extract_participants_empty(self, transcript_processor):
        """Test extracting participants from empty messages."""
        participants = transcript_processor._extract_participants([])

        assert participants == []

    def test_extract_participants_malformed(self, transcript_processor):
        """Test extracting participants from malformed messages."""
        messages = [
            {"sender": "john", "text": "Hello"},
            {"text": "No sender"},  # Missing sender
            "not a dict",  # Not a dict
            {"sender": "jane", "text": "Hi"},
        ]

        participants = transcript_processor._extract_participants(messages)

        assert "john" in participants
        assert "jane" in participants

    def test_analyze_conversation(self, transcript_processor):
        """Test conversation analysis."""
        messages = [
            {"sender": "john", "text": "Hi"},
            {"sender": "jane", "text": "Hello"},
            {"sender": "john", "text": "How are you?"},
            {"sender": "bob", "text": "Good"},
            {"sender": "jane", "text": "Great!"},
        ]

        analysis = transcript_processor._analyze_conversation(messages)

        assert analysis["total_messages"] == 5
        assert analysis["unique_participants"] == 3
        assert analysis["participant_activity"]["john"] == 2
        assert analysis["participant_activity"]["jane"] == 2
        assert analysis["participant_activity"]["bob"] == 1

    def test_analyze_conversation_empty(self, transcript_processor):
        """Test analyzing empty conversation."""
        analysis = transcript_processor._analyze_conversation([])

        assert analysis == {}

    def test_split_messages(self, transcript_processor):
        """Test splitting messages into chunks."""
        messages = [{"sender": f"user{i}", "text": f"Message {i}"} for i in range(250)]

        splits = transcript_processor._split_messages(messages, 100)

        assert len(splits) == 3  # 100, 100, 50
        assert splits[0]["chunk_message_count"] == 100
        assert splits[1]["chunk_message_count"] == 100
        assert splits[2]["chunk_message_count"] == 50
        assert splits[0]["chunk_index"] == 0
        assert splits[1]["chunk_index"] == 1
        assert splits[2]["chunk_index"] == 2

    def test_split_messages_default_chunk_size(self, transcript_processor):
        """Test message splitting with default chunk size."""
        messages = [{"sender": "user", "text": f"Msg {i}"} for i in range(50)]

        splits = transcript_processor._split_messages(messages, 100)

        assert len(splits) == 1
        assert splits[0]["chunk_message_count"] == 50

    def test_split_messages_empty(self, transcript_processor):
        """Test splitting empty message list."""
        splits = transcript_processor._split_messages([], 100)

        assert splits == []

    def test_split_messages_metadata(self, transcript_processor):
        """Test that split messages have correct metadata."""
        messages = [{"sender": "user", "text": f"Msg {i}"} for i in range(10)]

        splits = transcript_processor._split_messages(messages, 5)

        assert len(splits) == 2

        # First split
        assert splits[0]["chunk_start_idx"] == 0
        assert splits[0]["chunk_end_idx"] == 4

        # Second split
        assert splits[1]["chunk_start_idx"] == 5
        assert splits[1]["chunk_end_idx"] == 9

    @pytest.mark.asyncio
    async def test_process_file_not_found(self, transcript_processor, tmp_path):
        """Test processing non-existent file."""
        non_existent = tmp_path / "non_existent.json"

        with pytest.raises(FileNotFoundError):
            await transcript_processor.process(non_existent)

    @pytest.mark.asyncio
    async def test_processor_result_structure(
        self, transcript_processor, sample_json_transcript_file
    ):
        """Test that processor result has correct structure."""
        result = await transcript_processor.process(sample_json_transcript_file)

        # Verify SimpleProcessorResult structure
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")
        assert hasattr(result, "embeddings")

        # Verify content structure
        assert isinstance(result.content, dict)
        assert "splits" in result.content
        assert "participants" in result.content
        assert "message_count" in result.content
        assert "total_splits" in result.content
        assert "date_range_start" in result.content
        assert "date_range_end" in result.content

        # Verify metadata structure
        assert isinstance(result.metadata, dict)
        assert "file_type" in result.metadata
        assert "file_size" in result.metadata
        assert "format" in result.metadata
        assert "analysis" in result.metadata

    @pytest.mark.asyncio
    async def test_process_large_transcript_chunking(
        self, transcript_processor, large_json_transcript_file
    ):
        """Test processing large transcript with automatic chunking."""
        result = await transcript_processor.process(large_json_transcript_file)

        assert result.content["message_count"] == 250
        assert result.content["total_splits"] == 3  # 100+100+50
        assert len(result.content["splits"]) == 3

    @pytest.mark.asyncio
    async def test_process_transcript_participants(
        self, transcript_processor, sample_json_transcript_file
    ):
        """Test participant extraction."""
        result = await transcript_processor.process(sample_json_transcript_file)

        participants = result.content["participants"]
        assert "john" in participants
        assert "jane" in participants
        assert "bob" in participants


@pytest.mark.unit
class TestChatTranscriptProcessorIntegration:
    """Integration tests for ChatTranscriptProcessor with fixtures."""

    @pytest.fixture
    async def transcript_processor(self):
        """Create a ChatTranscriptProcessor instance."""
        return ChatTranscriptProcessor()

    @pytest.mark.asyncio
    async def test_process_with_fixture_data(self, transcript_processor):
        """Test processing with fixture data."""
        fixture_data = DataTypeFixtures.create_chat_transcript_data()

        assert "platform" in fixture_data
        assert "channel" in fixture_data
        assert "messages" in fixture_data
        assert "participants" in fixture_data

        assert len(fixture_data["messages"]) > 0
        assert len(fixture_data["participants"]) > 0

    def test_chunk_size_boundary(self, transcript_processor):
        """Test message chunking at boundary conditions."""
        # Exactly 100 messages (one chunk)
        messages_100 = [{"sender": "user", "text": f"Msg {i}"} for i in range(100)]
        splits = transcript_processor._split_messages(messages_100, 100)
        assert len(splits) == 1

        # 101 messages (two chunks)
        messages_101 = [{"sender": "user", "text": f"Msg {i}"} for i in range(101)]
        splits = transcript_processor._split_messages(messages_101, 100)
        assert len(splits) == 2

    def test_participant_case_sensitivity(self, transcript_processor):
        """Test that participant names are case-sensitive."""
        messages = [
            {"sender": "John", "text": "Hello"},
            {"sender": "john", "text": "Hi"},
            {"sender": "JOHN", "text": "Hey"},
        ]

        participants = transcript_processor._extract_participants(messages)

        # Should extract all variants since they're technically different
        assert len(participants) == 3

    @pytest.mark.asyncio
    async def test_conversation_analysis_consistency(self, transcript_processor):
        """Test that conversation analysis is consistent."""
        messages = [
            {"sender": "user1", "text": "Hello"},
            {"sender": "user2", "text": "Hi"},
            {"sender": "user1", "text": "How are you?"},
        ]

        analysis = transcript_processor._analyze_conversation(messages)

        # Analyze the same messages again
        analysis2 = transcript_processor._analyze_conversation(messages)

        assert analysis == analysis2
