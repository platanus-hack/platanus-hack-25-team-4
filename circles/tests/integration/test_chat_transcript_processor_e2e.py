"""
End-to-End Tests for ChatTranscriptProcessor.

These tests run the complete chat transcript processor pipeline with real data.
Marked with @pytest.mark.slow and @pytest.mark.e2e to allow skipping in CI.

Run with: pytest -m "e2e" tests/integration/test_chat_transcript_processor_e2e.py
"""

import asyncio
import json
import logging
from pathlib import Path

import pytest

from src.etl.processors.chat_transcript_processor import ChatTranscriptProcessor

logger = logging.getLogger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_json_transcript(tmp_path) -> Path:
    """Create a sample JSON chat transcript."""
    transcript_data = {
        "messages": [
            {
                "sender": "Alice",
                "text": "Hey! How's the new project going?",
                "timestamp": "2025-01-15T10:00:00Z",
            },
            {
                "sender": "Bob",
                "text": "Great! I'm working on the Python API integration.",
                "timestamp": "2025-01-15T10:01:00Z",
            },
            {
                "sender": "Alice",
                "text": "Nice! Are you using FastAPI or Django?",
                "timestamp": "2025-01-15T10:02:00Z",
            },
            {
                "sender": "Bob",
                "text": "FastAPI. It's much faster for our use case.",
                "timestamp": "2025-01-15T10:03:00Z",
            },
            {
                "sender": "Alice",
                "text": "Excellent choice! Let me know if you need help with the database setup.",
                "timestamp": "2025-01-15T10:04:00Z",
            },
            {
                "sender": "Bob",
                "text": "Thanks! I'm using PostgreSQL with SQLAlchemy.",
                "timestamp": "2025-01-15T10:05:00Z",
            },
        ],
        "metadata": {
            "date_start": "2025-01-15T10:00:00Z",
            "date_end": "2025-01-15T10:05:00Z",
            "chat_name": "Tech Discussion",
        },
    }

    transcript_path = tmp_path / "chat_transcript.json"
    transcript_path.write_text(json.dumps(transcript_data, indent=2))
    return transcript_path


@pytest.fixture
def sample_text_transcript(tmp_path) -> Path:
    """Create a sample text-based chat transcript."""
    transcript_content = """Alice: Hey! How's the new project going?
Bob: Great! I'm learning Python and building a web scraper.
Alice: That's awesome! What libraries are you using?
Bob: I'm using BeautifulSoup and requests for the scraping.
Alice: Nice! Have you considered using Scrapy for larger projects?
Bob: Not yet, but I'll definitely check it out. Thanks for the tip!
Alice: No problem! Let me know if you need any help with the code.
Bob: Will do! I'm also looking into FastAPI for the backend.
Alice: Good choice! FastAPI is excellent for building APIs quickly.
Bob: Yeah, I'm excited to learn more about it.
"""

    transcript_path = tmp_path / "chat_transcript.txt"
    transcript_path.write_text(transcript_content)
    return transcript_path


@pytest.fixture
def large_json_transcript(tmp_path) -> Path:
    """Create a large JSON transcript to test chunking (250+ messages)."""
    messages = []
    for i in range(250):
        messages.append(
            {
                "sender": f"User{i % 5}",  # 5 different users
                "text": f"This is message number {i} in the conversation.",
                "timestamp": f"2025-01-15T{10 + (i // 60):02d}:{i % 60:02d}:00Z",
            }
        )

    transcript_data = {
        "messages": messages,
        "metadata": {
            "date_start": "2025-01-15T10:00:00Z",
            "date_end": "2025-01-15T14:10:00Z",
            "chat_name": "Large Group Chat",
        },
    }

    transcript_path = tmp_path / "large_chat_transcript.json"
    transcript_path.write_text(json.dumps(transcript_data))
    return transcript_path


# ============================================================================
# ChatTranscriptProcessor E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestChatTranscriptProcessorE2E:
    """End-to-end tests for ChatTranscriptProcessor."""

    async def test_single_json_transcript_processing(self, sample_json_transcript):
        """
        E2E Test: Process a single JSON chat transcript end-to-end.

        Tests:
        - JSON file parsing
        - Message extraction
        - Participant identification
        - Conversation analysis
        - Metadata extraction
        - Result structure
        """
        processor = ChatTranscriptProcessor()
        result = await processor.process(sample_json_transcript)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "metadata")

        # Verify content fields
        assert "splits" in result.content
        assert "participants" in result.content
        assert "message_count" in result.content
        assert "total_splits" in result.content

        # Verify message count
        assert result.content["message_count"] == 6  # Our test has 6 messages

        # Verify participants
        participants = result.content["participants"]
        assert len(participants) == 2
        assert "Alice" in participants
        assert "Bob" in participants

        # Verify splits structure
        splits = result.content["splits"]
        assert isinstance(splits, list)
        assert len(splits) == 1  # 6 messages = 1 split (< 100 messages per split)

        # Verify first split
        first_split = splits[0]
        assert "messages" in first_split
        assert "chunk_index" in first_split
        assert "chunk_message_count" in first_split
        assert first_split["chunk_message_count"] == 6

        # Verify metadata
        assert result.metadata["file_type"] == ".json"
        assert result.metadata["format"] == "json"
        assert result.metadata["file_size"] > 0

        # Verify conversation analysis
        assert "analysis" in result.metadata
        analysis = result.metadata["analysis"]
        assert "total_messages" in analysis
        assert "unique_participants" in analysis
        assert "participant_activity" in analysis

        assert analysis["total_messages"] == 6
        assert analysis["unique_participants"] == 2

        # Verify participant activity counts
        activity = analysis["participant_activity"]
        assert "Alice" in activity
        assert "Bob" in activity
        assert activity["Alice"] == 3
        assert activity["Bob"] == 3

        logger.info("✓ Single JSON transcript processing succeeded")
        logger.info(f"  Messages: {result.content['message_count']}")
        logger.info(f"  Participants: {participants}")
        logger.info(f"  Splits: {result.content['total_splits']}")

    async def test_single_text_transcript_processing(self, sample_text_transcript):
        """
        E2E Test: Process a single text-based chat transcript.

        Tests:
        - Text file parsing
        - Line-based message extraction
        - Participant extraction from text format
        - Analysis of text-based conversations
        """
        processor = ChatTranscriptProcessor()
        result = await processor.process(sample_text_transcript)

        # Verify result structure
        assert result is not None
        assert "splits" in result.content
        assert "participants" in result.content
        assert "message_count" in result.content

        # Verify message count (10 lines in our test transcript)
        assert result.content["message_count"] == 10

        # Verify participants
        participants = result.content["participants"]
        assert len(participants) == 2
        assert "Alice" in participants
        assert "Bob" in participants

        # Verify metadata
        assert result.metadata["file_type"] == ".txt"
        assert result.metadata["format"] == "text"

        # Verify conversation analysis
        analysis = result.metadata["analysis"]
        assert analysis["total_messages"] == 10
        assert analysis["unique_participants"] == 2

        logger.info("✓ Single text transcript processing succeeded")
        logger.info(f"  Messages: {result.content['message_count']}")
        logger.info(f"  Participants: {participants}")
        logger.info(f"  Format: {result.metadata['format']}")

    async def test_large_transcript_chunking(self, large_json_transcript):
        """
        E2E Test: Process large transcript and verify chunking behavior.

        Tests:
        - Large file processing (250+ messages)
        - Automatic message chunking (100 messages per chunk)
        - Chunk metadata
        - Chunk boundaries
        - Participant tracking across chunks
        """
        processor = ChatTranscriptProcessor()
        result = await processor.process(large_json_transcript)

        # Verify chunking occurred
        assert result.content["message_count"] == 250
        assert result.content["total_splits"] == 3  # 250 messages / 100 = 3 chunks

        # Verify splits structure
        splits = result.content["splits"]
        assert len(splits) == 3

        # Verify chunk sizes
        assert splits[0]["chunk_message_count"] == 100  # First chunk
        assert splits[1]["chunk_message_count"] == 100  # Second chunk
        assert splits[2]["chunk_message_count"] == 50  # Last chunk (remainder)

        # Verify chunk indices
        assert splits[0]["chunk_index"] == 0
        assert splits[1]["chunk_index"] == 1
        assert splits[2]["chunk_index"] == 2

        # Verify chunk boundaries
        assert splits[0]["chunk_start_idx"] == 0
        assert splits[0]["chunk_end_idx"] == 99
        assert splits[1]["chunk_start_idx"] == 100
        assert splits[1]["chunk_end_idx"] == 199
        assert splits[2]["chunk_start_idx"] == 200
        assert splits[2]["chunk_end_idx"] == 249

        # Verify participants (5 different users: User0-User4)
        participants = result.content["participants"]
        assert len(participants) == 5
        assert all(f"User{i}" in participants for i in range(5))

        logger.info("✓ Large transcript chunking test succeeded")
        logger.info(f"  Total messages: {result.content['message_count']}")
        logger.info(f"  Total chunks: {result.content['total_splits']}")
        logger.info(f"  Chunk sizes: {[s['chunk_message_count'] for s in splits]}")

    async def test_batch_transcript_processing(self, tmp_path):
        """
        E2E Test: Process multiple transcript files in parallel.

        Tests:
        - Batch file processing
        - Concurrency control with semaphore
        - Mixed format handling (JSON + TXT)
        - Result aggregation
        - Error handling in batch
        """
        # Create multiple test transcripts
        transcript_paths = []

        # Create JSON transcripts
        for i in range(3):
            messages = [
                {
                    "sender": f"User{j}",
                    "text": f"Message {j} in conversation {i}",
                }
                for j in range(5)
            ]
            transcript_data = {"messages": messages}

            transcript_path = tmp_path / f"transcript_{i}.json"
            transcript_path.write_text(json.dumps(transcript_data))
            transcript_paths.append(transcript_path)

        # Create text transcripts
        for i in range(2):
            content = "\n".join([f"User{j}: Message {j} in conversation {i + 3}" for j in range(5)])
            transcript_path = tmp_path / f"transcript_{i + 3}.txt"
            transcript_path.write_text(content)
            transcript_paths.append(transcript_path)

        # Process batch
        processor = ChatTranscriptProcessor(max_concurrent=3)
        results = await processor.process_batch(transcript_paths)

        # Verify batch processing
        assert len(results) == 5
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "metadata") for r in results)

        # Verify all have required fields
        assert all("message_count" in r.content for r in results)
        assert all("participants" in r.content for r in results)

        # Count successful vs failed
        successful = sum(1 for r in results if "processing_error" not in r.metadata)

        # Verify format detection
        json_results = [r for r in results if r.metadata.get("format") == "json"]
        text_results = [r for r in results if r.metadata.get("format") == "text"]

        assert len(json_results) == 3
        assert len(text_results) == 2

        logger.info("✓ Batch transcript processing succeeded")
        logger.info(f"  Processed {len(results)} transcripts with max_concurrent=3")
        logger.info(f"  Successful: {successful}/{len(results)}")
        logger.info(f"  JSON: {len(json_results)}, Text: {len(text_results)}")

    async def test_conversation_analysis_quality(self, sample_json_transcript):
        """
        E2E Test: Verify conversation analysis accuracy.

        Tests:
        - Participant activity tracking
        - Message distribution analysis
        - Conversation pattern detection
        - Metadata completeness
        """
        processor = ChatTranscriptProcessor()
        result = await processor.process(sample_json_transcript)

        # Get analysis
        analysis = result.metadata["analysis"]

        # Verify analysis completeness
        assert "total_messages" in analysis
        assert "unique_participants" in analysis
        assert "participant_activity" in analysis

        # Verify participant activity is accurate
        activity = analysis["participant_activity"]

        # Both Alice and Bob sent 3 messages each
        assert activity.get("Alice") == 3
        assert activity.get("Bob") == 3

        # Verify totals match
        total_from_activity = sum(activity.values())
        assert total_from_activity == analysis["total_messages"]
        assert total_from_activity == result.content["message_count"]

        logger.info("✓ Conversation analysis quality test succeeded")
        logger.info(f"  Total messages: {analysis['total_messages']}")
        logger.info(f"  Unique participants: {analysis['unique_participants']}")
        logger.info(f"  Participant activity: {activity}")

    async def test_empty_file_handling(self, tmp_path):
        """
        E2E Test: Verify proper error handling for empty files.

        Tests:
        - Empty file detection
        - Appropriate error messages
        - Error result structure
        """
        # Create empty file
        empty_file = tmp_path / "empty_transcript.json"
        empty_file.write_text("")

        processor = ChatTranscriptProcessor()

        # Should raise ValueError for empty file
        with pytest.raises(ValueError, match="empty"):
            await processor.process(empty_file)

        logger.info("✓ Empty file handling test succeeded")

    async def test_invalid_json_handling(self, tmp_path):
        """
        E2E Test: Verify handling of invalid JSON format.

        Tests:
        - Invalid JSON detection
        - Graceful error handling
        - Fallback behavior
        """
        # Create file with invalid JSON
        invalid_json_file = tmp_path / "invalid_transcript.json"
        invalid_json_file.write_text("{ this is not valid json }")

        processor = ChatTranscriptProcessor()
        result = await processor.process(invalid_json_file)

        # Should process but return empty messages list
        assert result.content["message_count"] == 0
        assert len(result.content["participants"]) == 0

        logger.info("✓ Invalid JSON handling test succeeded")


# ============================================================================
# Parallel Processing Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.e2e
class TestChatTranscriptProcessorParallel:
    """Test parallel processing capabilities."""

    async def test_parallel_batch_processing(self, tmp_path):
        """
        E2E Test: Verify parallel processing with concurrency control.

        Tests:
        - Semaphore-based concurrency limiting
        - Parallel file I/O
        - Throughput optimization
        - Resource management
        """
        # Create batch of transcripts
        transcript_paths = []
        for i in range(10):
            messages = [
                {
                    "sender": f"User{j % 3}",
                    "text": f"Message {j} in batch conversation {i}",
                }
                for j in range(20)
            ]
            transcript_data = {"messages": messages}

            transcript_path = tmp_path / f"batch_transcript_{i}.json"
            transcript_path.write_text(json.dumps(transcript_data))
            transcript_paths.append(transcript_path)

        # Process with concurrency limit
        processor = ChatTranscriptProcessor(max_concurrent=5)
        results = await processor.process_batch(transcript_paths)

        # Verify all files were processed
        assert len(results) == 10

        # Verify results structure
        for result in results:
            assert hasattr(result, "content")
            assert hasattr(result, "metadata")
            assert result.content["message_count"] == 20
            assert len(result.content["participants"]) == 3

        successful = sum(1 for r in results if "processing_error" not in r.metadata)

        logger.info("✓ Parallel batch processing succeeded")
        logger.info(f"  Processed {len(results)} files in parallel")
        logger.info(f"  Successful: {successful}/{len(results)}")
        logger.info(f"  Concurrency limit: {processor.max_concurrent}")

    async def test_mixed_format_batch_processing(self, tmp_path):
        """
        E2E Test: Process batch with mixed JSON and text formats.

        Tests:
        - Format detection
        - Mixed format handling
        - Consistent result structure across formats
        """
        transcript_paths = []

        # Create 5 JSON files
        for i in range(5):
            messages = [{"sender": "Alice", "text": f"JSON message {j}"} for j in range(10)]
            path = tmp_path / f"json_transcript_{i}.json"
            path.write_text(json.dumps({"messages": messages}))
            transcript_paths.append(path)

        # Create 5 text files
        for i in range(5):
            content = "\n".join([f"Alice: Text message {j}" for j in range(10)])
            path = tmp_path / f"text_transcript_{i}.txt"
            path.write_text(content)
            transcript_paths.append(path)

        processor = ChatTranscriptProcessor(max_concurrent=5)
        results = await processor.process_batch(transcript_paths)

        # Verify all processed
        assert len(results) == 10

        # Verify format distribution
        json_count = sum(1 for r in results if r.metadata.get("format") == "json")
        text_count = sum(1 for r in results if r.metadata.get("format") == "text")

        assert json_count == 5
        assert text_count == 5

        # Verify all have consistent structure
        for result in results:
            assert "message_count" in result.content
            assert "participants" in result.content
            assert "splits" in result.content
            assert result.content["message_count"] == 10

        logger.info("✓ Mixed format batch processing succeeded")
        logger.info(f"  JSON files: {json_count}")
        logger.info(f"  Text files: {text_count}")
