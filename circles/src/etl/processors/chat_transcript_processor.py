"""
Chat Transcript Processor - Parse and analyze chat conversation data.

Extracts:
- Conversation structure and flow
- Participant information and activity
- Message metadata and conversation patterns
- Support for JSON and text-based formats

Handles batch processing with concurrency control and comprehensive error handling.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SimpleProcessorResult:
    """Simple result container for processor outputs."""

    content: Dict[str, Any]
    metadata: Dict[str, Any]
    embeddings: Optional[Dict[str, Any]] = None


class ChatTranscriptProcessor:
    """Process chat transcript files (JSON or TXT format) with batch processing support."""

    MESSAGES_PER_CHUNK = 100

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize processor with concurrency control.

        Args:
            max_concurrent: Maximum concurrent transcript file processing (default 5)
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process chat transcript file asynchronously.

        Args:
            file_path: Path to transcript file (JSON or TXT)

        Returns:
            SimpleProcessorResult with parsed transcript data, split into chunks if needed

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid format
        """
        try:
            # Check file exists
            if not file_path.exists():
                raise FileNotFoundError(f"Transcript file not found: {file_path}")

            # Read file content asynchronously
            def _read_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

            content_str = await asyncio.to_thread(_read_file)

            # Validate file has content
            if not content_str.strip():
                raise ValueError("Transcript file appears to be empty")

            # Parse based on format
            if file_path.suffix.lower() == ".json":
                messages, metadata = self._parse_json_transcript(content_str)
            else:
                messages, metadata = self._parse_text_transcript(content_str)

            # Extract participants
            participants = self._extract_participants(messages)

            # Analyze conversation
            analysis = self._analyze_conversation(messages)

            # Split messages into chunks if needed
            splits = self._split_messages(messages, self.MESSAGES_PER_CHUNK)

            # Get file size asynchronously
            file_size = (await asyncio.to_thread(file_path.stat)).st_size

            result_content = {
                "splits": splits,
                "participants": participants,
                "message_count": len(messages),
                "total_splits": len(splits),
                "date_range_start": metadata.get("date_start"),
                "date_range_end": metadata.get("date_end"),
            }

            metadata_result = {
                "file_type": file_path.suffix.lower(),
                "file_size": file_size,
                "format": "json" if file_path.suffix.lower() == ".json" else "text",
                "analysis": analysis,
            }

            return SimpleProcessorResult(
                content=result_content, metadata=metadata_result
            )

        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid transcript file {file_path.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing transcript file {file_path.name}: {e}")
            raise

    @staticmethod
    def _parse_json_transcript(content: str) -> tuple[list, dict]:
        """Parse JSON-formatted transcript."""
        try:
            data = json.loads(content)
            if isinstance(data, list):
                messages = data
            elif isinstance(data, dict) and "messages" in data:
                messages = data["messages"]
            else:
                messages = []

            metadata = {"date_start": None, "date_end": None}
            if isinstance(data, dict):
                metadata.update(data.get("metadata", {}))

            return messages, metadata
        except json.JSONDecodeError:
            return [], {"date_start": None, "date_end": None}

    @staticmethod
    def _parse_text_transcript(content: str) -> tuple[list, dict]:
        """Parse text-formatted transcript (simple line-based format)."""
        messages = []
        lines = content.split("\n")

        for line in lines:
            if ":" in line:
                parts = line.split(":", 1)
                messages.append({"sender": parts[0].strip(), "text": parts[1].strip()})

        metadata = {"date_start": None, "date_end": None}
        return messages, metadata

    @staticmethod
    def _extract_participants(messages: list) -> list[str]:
        """Extract unique participants from messages."""
        participants = set()
        for msg in messages:
            if isinstance(msg, dict) and "sender" in msg:
                participants.add(msg["sender"])
        return list(participants)

    @staticmethod
    def _analyze_conversation(messages: list) -> dict:
        """Analyze conversation patterns."""
        if not messages:
            return {}

        total_messages = len(messages)
        participant_counts = {}

        for msg in messages:
            if isinstance(msg, dict) and "sender" in msg:
                sender = msg["sender"]
                participant_counts[sender] = participant_counts.get(sender, 0) + 1

        return {
            "total_messages": total_messages,
            "unique_participants": len(participant_counts),
            "participant_activity": participant_counts,
        }

    @staticmethod
    def _split_messages(messages: list, chunk_size: int) -> list[dict]:
        """
        Split messages into chunks of specified size.

        Args:
            messages: List of message dictionaries
            chunk_size: Maximum number of messages per chunk

        Returns:
            List of chunk dictionaries, each containing messages and metadata
        """
        if not messages:
            return []

        splits = []
        total_messages = len(messages)

        for i in range(0, total_messages, chunk_size):
            chunk_messages = messages[i : i + chunk_size]
            chunk_start_idx = i
            chunk_end_idx = min(i + chunk_size - 1, total_messages - 1)

            chunk_data = {
                "messages": chunk_messages,
                "chunk_index": len(splits),
                "chunk_start_idx": chunk_start_idx,
                "chunk_end_idx": chunk_end_idx,
                "chunk_message_count": len(chunk_messages),
            }

            splits.append(chunk_data)

        return splits

    async def process_batch(
        self, file_paths: List[Path]
    ) -> List[SimpleProcessorResult]:
        """
        Process multiple transcript files in parallel with concurrency control.

        Uses semaphore to limit concurrent file processing while maximizing throughput.

        Args:
            file_paths: List of transcript file paths

        Returns:
            List of SimpleProcessorResult for each transcript file

        Note:
            Failures are captured in results with error metadata instead of raising.
            This allows batch processing to continue even if some files fail.
        """
        logger.info(
            f"Processing batch of {len(file_paths)} transcript files "
            f"(max {self.max_concurrent} concurrent)"
        )

        # Create tasks with semaphore control
        tasks = [self._process_with_semaphore(file_path) for file_path in file_paths]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results - convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Error processing transcript {file_paths[i].name}: {result}"
                )
                # Create error result with fallback data
                error_result = SimpleProcessorResult(
                    content={
                        "splits": [],
                        "participants": [],
                        "message_count": 0,
                        "total_splits": 0,
                        "date_range_start": None,
                        "date_range_end": None,
                    },
                    metadata={
                        "file_type": file_paths[i].suffix.lower(),
                        "file_size": 0,
                        "format": "unknown",
                        "analysis": {},
                        "processing_error": str(result),
                    },
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)

        successful = len(
            [r for r in processed_results if "processing_error" not in r.metadata]
        )
        failed = len(processed_results) - successful

        logger.info(
            f"Batch processing complete: {successful} successful, {failed} failed"
        )
        return processed_results

    async def _process_with_semaphore(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process transcript with semaphore to control concurrency.

        Args:
            file_path: Path to transcript file

        Returns:
            SimpleProcessorResult

        Raises:
            Exception if processing fails (caught by gather in process_batch)
        """
        async with self.semaphore:
            return await self.process(file_path)
