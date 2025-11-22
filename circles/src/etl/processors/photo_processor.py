"""
Photo Processor - Handles image file processing using Claude Vision API.

Extracts:
- Visual captions via Claude's vision capabilities
- Detailed analysis of image content
- EXIF metadata (if available)
"""

import asyncio
import base64
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import anthropic

from ..core import get_settings

logger = logging.getLogger(__name__)


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


class PhotoProcessor:
    """Process images using Claude Vision API."""

    def __init__(self):
        """Initialize processor with Anthropic client."""
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def process(self, file_path: Path) -> SimpleProcessorResult:
        """
        Process image file with Claude Vision API.

        Args:
            file_path: Path to image file

        Returns:
            SimpleProcessorResult with vision analysis and metadata
        """
        try:
            # Read image file asynchronously
            async with aiofiles.open(file_path, "rb") as f:
                image_data = await f.read()

            # Encode to base64
            encoded_image = base64.standard_b64encode(image_data).decode("utf-8")

            # Determine media type from extension
            media_type = self._get_media_type(file_path)

            # Get vision analysis from Claude (non-blocking)
            caption, analysis = await self._analyze_image(encoded_image, media_type)

            # Extract EXIF data asynchronously
            exif_data = await self._extract_exif_data_async(file_path)

            # Get file stats asynchronously
            file_size = (await asyncio.to_thread(file_path.stat)).st_size

            # Build result
            content = {
                "caption": caption,
                "analysis": analysis,
                "image_file": file_path.name,
            }

            metadata = {
                "file_type": file_path.suffix.lower(),
                "file_size": file_size,
                "exif_data": exif_data,
            }

            return SimpleProcessorResult(content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error processing image {file_path.name}: {e}")
            raise

    async def _analyze_image(
        self, encoded_image: str, media_type: str
    ) -> tuple[str, Dict[str, Any]]:
        """
        Analyze image using Claude Vision API (non-blocking).

        Returns:
            Tuple of (caption, analysis_dict)
        """
        try:
            # Run blocking API call in thread pool
            def _api_call():
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": encoded_image,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": """Analyze this image and provide:
1. A brief one-line caption describing what you see
2. A detailed analysis including:
   - Main objects/subjects
   - Setting/environment
   - Colors and composition
   - Any text visible
   - Estimated date/time context if visible
   - Any notable details

Format your response as JSON with keys: caption (string) and analysis (object with the analysis details).""",
                                },
                            ],
                        }
                    ],
                )

            # Execute in thread pool to avoid blocking
            message = await asyncio.to_thread(_api_call)

            # Parse response
            response_text = message.content[0].text

            # Try to extract JSON from response
            try:
                # Use regex to find JSON object more reliably
                json_match = re.search(
                    r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text, re.DOTALL
                )
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                    caption = result.get("caption", "")
                    analysis = result.get("analysis", {})
                else:
                    # Fallback if no JSON found
                    caption = (
                        response_text.split("\n")[0]
                        if response_text
                        else "Unable to analyze"
                    )
                    analysis = {"raw_response": response_text}
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Claude response: {e}")
                caption = (
                    response_text.split("\n")[0]
                    if response_text
                    else "Unable to analyze"
                )
                analysis = {"raw_response": response_text, "parse_error": str(e)}

            return caption, analysis

        except anthropic.APIError as e:
            logger.error(f"Claude Vision API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in image analysis: {e}")
            raise

    @staticmethod
    def _get_media_type(file_path: Path) -> str:
        """Get MIME type from file extension."""
        extension = file_path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".heic": "image/heic",
        }
        return media_types.get(extension, "image/jpeg")

    @staticmethod
    async def _extract_exif_data_async(file_path: Path) -> Dict[str, Any]:
        """
        Extract EXIF data from image asynchronously.

        Returns empty dict if PIL not available or no EXIF data.
        """

        def _extract_exif():
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS

                image = Image.open(file_path)
                exif_dict = {}

                if hasattr(image, "_getexif"):
                    exif_data = image._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            exif_dict[tag_name] = str(value)[
                                :100
                            ]  # Limit string length

                return exif_dict
            except Exception as e:
                logger.debug(f"Could not extract EXIF data: {e}")
                return {}

        # Run EXIF extraction in thread pool
        return await asyncio.to_thread(_extract_exif)

    @staticmethod
    def _extract_exif_data(file_path: Path) -> Dict[str, Any]:
        """
        Extract EXIF data from image (synchronous version for backward compatibility).

        Returns empty dict if PIL not available or no EXIF data.
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS

            image = Image.open(file_path)
            exif_dict = {}

            if hasattr(image, "_getexif"):
                exif_data = image._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        exif_dict[tag_name] = str(value)[:100]  # Limit string length

            return exif_dict
        except Exception:
            # PIL not available or image doesn't have EXIF
            return {}
