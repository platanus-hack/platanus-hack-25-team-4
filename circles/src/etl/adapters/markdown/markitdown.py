"""MarkItDown adapter implementation for markdown conversion.

This module provides a markdown converter adapter using the markitdown library,
supporting conversion from PDF, DOCX, PPTX, XLSX, images, audio, HTML, and ZIP files.
"""

import asyncio
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from ..base import ConversionError, InvalidInputError, UnsupportedFormatError


@dataclass
class MarkItDownConfig:
    """Configuration for MarkItDown adapter.

    Attributes:
        enable_llm: Whether to enable LLM-based features for enhanced conversion.
        llm_model: LLM model to use if enable_llm is True.
        llm_api_key: API key for LLM service if enable_llm is True.
    """

    enable_llm: bool = False
    llm_model: str | None = None
    llm_api_key: str | None = None


class MarkItDownAdapter:
    """Markdown converter using the markitdown library.

    This adapter provides async conversion capabilities for various file formats
    to markdown, including PDF, Office documents, images, and more.

    Supported formats:
        - PDF (.pdf)
        - Microsoft Word (.docx)
        - Microsoft PowerPoint (.pptx)
        - Microsoft Excel (.xlsx)
        - Images (.jpg, .jpeg, .png, .gif, .bmp, .tiff)
        - Audio (.mp3, .wav, .m4a)
        - HTML (.html, .htm)
        - ZIP archives (.zip)
        - Plain text (.txt, .md)

    Example:
        ```python
        adapter = MarkItDownAdapter()
        markdown = await adapter.convert("document.pdf")
        print(markdown)
        ```
    """

    # Supported file extensions
    SUPPORTED_FORMATS = [
        "pdf",
        "docx",
        "pptx",
        "xlsx",
        "jpg",
        "jpeg",
        "png",
        "gif",
        "bmp",
        "tiff",
        "mp3",
        "wav",
        "m4a",
        "html",
        "htm",
        "zip",
        "txt",
        "md",
    ]

    def __init__(self, config: MarkItDownConfig | None = None) -> None:
        """Initialize the MarkItDown adapter.

        Args:
            config: Configuration for the adapter. Uses defaults if None.
        """
        self.config = config or MarkItDownConfig()
        self._converter: Any | None = None
        self._lock = asyncio.Lock()

    async def _ensure_converter_loaded(self) -> None:
        """Ensure the markitdown converter is initialized (lazy loading).

        Raises:
            ConversionError: If converter initialization fails.
        """
        if self._converter is not None:
            return

        async with self._lock:
            # Double-check after acquiring lock
            if self._converter is not None:
                return

            try:
                from markitdown import MarkItDown

                # Initialize converter
                loop = asyncio.get_event_loop()
                self._converter = await loop.run_in_executor(
                    None,
                    lambda: MarkItDown(
                        llm_client=None,  # Can be configured for LLM features
                        llm_model=self.config.llm_model,
                    ),
                )

            except ImportError as e:
                raise ConversionError(
                    "markitdown library not installed. "
                    "Install with: pip install markitdown[all]"
                ) from e
            except Exception as e:
                raise ConversionError(f"Failed to initialize MarkItDown: {e}") from e

    def _detect_file_type(self, path: Path) -> str:
        """Detect file type from file extension.

        Args:
            path: Path to the file.

        Returns:
            File extension without the dot (e.g., 'pdf', 'docx').

        Raises:
            UnsupportedFormatError: If file type is not supported.
        """
        extension = path.suffix.lstrip(".").lower()

        if not extension:
            raise UnsupportedFormatError(f"File has no extension: {path}")

        if extension not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        return extension

    async def convert(
        self,
        source: Path | bytes,
        source_type: str | None = None,
    ) -> str:
        """Convert a file to markdown format.

        Args:
            source: Path to source file or raw file bytes.
            source_type: Optional file type hint (e.g., 'pdf', 'docx').

        Returns:
            Converted markdown content as string.

        Raises:
            ConversionError: If conversion fails.
            UnsupportedFormatError: If file format is not supported.
            InvalidInputError: If source is invalid.
        """
        await self._ensure_converter_loaded()

        try:
            # Handle Path input
            if isinstance(source, (Path, str)):
                path = Path(source)
                if not path.exists():
                    raise InvalidInputError(f"File not found: {path}")
                if not path.is_file():
                    raise InvalidInputError(f"Not a file: {path}")

                # Validate file type
                if source_type:
                    if source_type.lstrip(".").lower() not in self.SUPPORTED_FORMATS:
                        raise UnsupportedFormatError(
                            f"Unsupported format: {source_type}"
                        )
                else:
                    self._detect_file_type(path)

                # Convert using file path
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: self._converter.convert(str(path))
                )

            # Handle bytes input
            else:
                if not source_type:
                    raise InvalidInputError(
                        "source_type is required when source is bytes"
                    )

                # Validate source type
                ext = source_type.lstrip(".").lower()
                if ext not in self.SUPPORTED_FORMATS:
                    raise UnsupportedFormatError(f"Unsupported format: {source_type}")

                # Convert using BytesIO
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._converter.convert_stream(
                        BytesIO(source), file_extension=f".{ext}"
                    ),
                )

            # Extract markdown text from result
            if hasattr(result, "text_content"):
                return result.text_content
            else:
                return str(result)

        except (ConversionError, UnsupportedFormatError, InvalidInputError):
            raise
        except Exception as e:
            raise ConversionError(f"Conversion failed: {e}") from e

    async def convert_batch(
        self,
        sources: list[Path | bytes],
        source_types: list[str | None] | None = None,
    ) -> list[str]:
        """Convert multiple files to markdown in batch.

        Args:
            sources: List of file paths or raw file bytes.
            source_types: Optional list of type hints for each source.

        Returns:
            List of converted markdown content strings.

        Raises:
            ConversionError: If any conversion fails.
            UnsupportedFormatError: If any file format is not supported.
            InvalidInputError: If any source is invalid.
            ValueError: If sources and source_types have different lengths.
        """
        if source_types is not None and len(sources) != len(source_types):
            raise ValueError(
                f"Number of sources ({len(sources)}) must match "
                f"number of source_types ({len(source_types)})"
            )

        # Prepare source types list
        types = source_types if source_types is not None else [None] * len(sources)

        # Convert all sources concurrently
        results = await asyncio.gather(
            *[
                self.convert(source, source_type)
                for source, source_type in zip(sources, types)
            ]
        )

        return list(results)

    async def supported_formats(self) -> list[str]:
        """Get list of supported file formats.

        Returns:
            List of supported file extensions.
        """
        return self.SUPPORTED_FORMATS.copy()
