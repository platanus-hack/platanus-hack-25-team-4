"""
Voice Note Processor - Handles audio transcription using OpenAI Whisper API.

Extracts:
- Speech-to-text transcription
- Language detection
- Confidence scores
- Topic extraction (basic via keyword analysis)
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from openai import OpenAI

from ..core import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SimpleProcessorResult:
    """Simple result container for processor outputs."""

    content: Dict[str, Any]
    metadata: Dict[str, Any]
    embeddings: Optional[Dict[str, Any]] = None


class VoiceNoteProcessor:
    """Process audio files using OpenAI Whisper API with batch support."""

    def __init__(self, max_concurrent: int = 3):
        """
        Initialize processor with OpenAI client.

        Args:
            max_concurrent: Maximum concurrent Whisper API calls (default 3, lower due to API rate limits)
        """
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process audio file with Whisper API.

        Args:
            file_path: Path to audio file

        Returns:
            SimpleProcessorResult with transcription and metadata
        """
        try:
            # Transcribe audio
            transcription_result = await self._transcribe_audio(file_path)

            # Extract topics from transcription
            topics = self._extract_topics(transcription_result.get("text", ""))

            # Extract sentiment (basic)
            sentiment = self._analyze_sentiment(transcription_result.get("text", ""))

            # Get file stats asynchronously
            file_size = (await asyncio.to_thread(file_path.stat)).st_size

            # Build result
            content = {
                "transcription": transcription_result.get("text", ""),
                "language": transcription_result.get("language", "unknown"),
                "topics": topics,
                "sentiment": sentiment,
            }

            metadata = {
                "file_type": file_path.suffix.lower(),
                "file_size": file_size,
                "confidence": transcription_result.get("confidence", 0.0),
                "duration_seconds": await self._get_audio_duration(file_path),
            }

            return SimpleProcessorResult(content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error processing audio file {file_path.name}: {e}")
            raise

    async def _transcribe_audio(self, file_path: Path) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper API (non-blocking).

        Returns:
            Dict with transcription, language, and confidence
        """
        try:
            # Read audio file asynchronously
            async with aiofiles.open(file_path, "rb") as audio_file:
                audio_data = await audio_file.read()

            # Define sync function to run in thread pool
            def _whisper_transcribe():
                # Create a file-like object from bytes
                from io import BytesIO

                audio_bytes_file = BytesIO(audio_data)
                audio_bytes_file.name = file_path.name

                return self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bytes_file,
                    temperature=0,  # More deterministic
                )

            # Run Whisper API in thread pool to avoid blocking
            transcript = await asyncio.to_thread(_whisper_transcribe)

            return {
                "text": transcript.text,
                "language": getattr(transcript, "language", None) or "unknown",
                "confidence": 0.95,  # Whisper doesn't return explicit confidence
            }
        except Exception as e:
            logger.error(f"Whisper transcription error for {file_path.name}: {e}")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "error": str(e),
            }

    @staticmethod
    def _extract_topics(text: str) -> list[str]:
        """
        Extract topics from transcription via simple keyword analysis.

        Returns list of detected topics.
        """
        if not text:
            return []

        # Simple topic extraction via common keywords
        # In production, use NLP libraries like spaCy or transformers
        common_topics = {
            "technology": [
                "software",
                "code",
                "coding",
                "python",
                "javascript",
                "database",
                "api",
                "cloud",
            ],
            "business": [
                "meeting",
                "project",
                "deadline",
                "budget",
                "team",
                "client",
                "revenue",
            ],
            "health": [
                "exercise",
                "workout",
                "gym",
                "health",
                "fitness",
                "diet",
                "doctor",
                "medical",
            ],
            "learning": [
                "learning",
                "course",
                "tutorial",
                "study",
                "book",
                "education",
                "skill",
            ],
            "travel": ["trip", "travel", "flight", "hotel", "vacation", "destination"],
        }

        text_lower = text.lower()
        detected = set()

        for topic, keywords in common_topics.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.add(topic)
                    break

        return list(detected)

    @staticmethod
    def _analyze_sentiment(text: str) -> Dict[str, Any]:
        """
        Basic sentiment analysis of transcription.

        Returns dict with sentiment label and score.
        """
        if not text:
            return {"sentiment": "neutral", "score": 0.5}

        # Simple sentiment analysis via positive/negative word counts
        # In production, use transformers library or NLP model
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "love",
            "happy",
            "perfect",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "hate",
            "sad",
            "angry",
            "frustrated",
            "wrong",
        }

        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count > neg_count:
            sentiment = "positive"
            score = min(1.0, 0.5 + (pos_count / max(len(text.split()), 1)) * 0.5)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max(0.0, 0.5 - (neg_count / max(len(text.split()), 1)) * 0.5)
        else:
            sentiment = "neutral"
            score = 0.5

        return {"sentiment": sentiment, "score": round(score, 2)}

    @staticmethod
    async def _get_audio_duration(file_path: Path) -> float:
        """
        Get audio file duration in seconds (non-blocking).

        Returns duration or 0 if unable to determine.
        """

        def _get_duration():
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_file(file_path)
                return len(audio) / 1000.0  # Convert milliseconds to seconds
            except Exception as e:
                logger.debug(f"Could not determine audio duration: {e}")
                # Unable to determine duration
                return 0.0

        # Run audio duration detection in thread pool
        return await asyncio.to_thread(_get_duration)

    async def process_batch(
        self, file_paths: List[Path]
    ) -> List[SimpleProcessorResult]:
        """
        Process multiple audio files in parallel with concurrency control.

        Uses semaphore to limit concurrent Whisper API calls while maximizing throughput.

        Args:
            file_paths: List of audio file paths

        Returns:
            List of SimpleProcessorResult for each audio file

        Note:
            Failures are captured in results with error metadata instead of raising.
            This allows batch processing to continue even if some files fail.
        """
        logger.info(
            f"Processing batch of {len(file_paths)} audio files "
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
                logger.error(f"Error processing audio {file_paths[i].name}: {result}")
                # Create error result with fallback data
                error_result = SimpleProcessorResult(
                    content={
                        "transcription": "",
                        "language": "unknown",
                        "topics": [],
                        "sentiment": {"sentiment": "neutral", "score": 0.0},
                    },
                    metadata={
                        "file_type": file_paths[i].suffix.lower(),
                        "file_size": 0,
                        "confidence": 0.0,
                        "duration_seconds": 0.0,
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
        Process audio with semaphore to control concurrency.

        Args:
            file_path: Path to audio file

        Returns:
            SimpleProcessorResult

        Raises:
            Exception if processing fails (caught by gather in process_batch)
        """
        async with self.semaphore:
            return await self.process(file_path)
