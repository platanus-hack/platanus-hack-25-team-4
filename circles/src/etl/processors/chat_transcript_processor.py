"""
Chat Transcript Processor - Parse and analyze chat conversation data.

Extracts:
- Conversation structure
- Participant information
- Message metadata and patterns
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class SimpleProcessorResult:
    """Simple result container for processor outputs."""

    def __init__(
        self,
        content: Dict[str, Any],
        metadata: Dict[str, Any],
        embeddings: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.metadata = metadata
        self.embeddings = embeddings or {}


class ChatTranscriptProcessor:
    """Process chat transcript files (JSON or TXT format)."""

    MESSAGES_PER_CHUNK = 100

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process chat transcript file.

        Args:
            file_path: Path to transcript file (JSON or TXT)

        Returns:
            SimpleProcessorResult with parsed transcript data, split into chunks if needed
        """
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content_str = f.read()

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

        result_content = {
            "splits": splits,
            "participants": participants,
            "message_count": len(messages),
            "total_splits": len(splits),
            "date_range_start": metadata.get("date_start"),
            "date_range_end": metadata.get("date_end"),
        }

        return SimpleProcessorResult(
            content=result_content,
            metadata={
                "file_type": file_path.suffix.lower(),
                "file_size": file_path.stat().st_size,
                "format": "json" if file_path.suffix.lower() == ".json" else "text",
                "analysis": analysis,
            },
        )

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
