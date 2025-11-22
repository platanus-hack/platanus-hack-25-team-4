"""Protocol definition for Markdown converter adapters.

This module defines the MarkdownConverter protocol that all markdown conversion
implementations must follow for consistent integration in the ETL pipeline.
"""

from pathlib import Path
from typing import Protocol


class MarkdownConverter(Protocol):
    """Protocol for Markdown converter adapters.

    Markdown converters provide a consistent interface for converting various
    file formats (PDF, DOCX, PPTX, images, etc.) to markdown format. Implementations
    should support both single and batch conversion operations asynchronously.
    """

    async def convert(
        self,
        source: Path | bytes,
        source_type: str | None = None,
    ) -> str:
        """Convert a file to markdown format.

        Args:
            source: Path to source file or raw file bytes.
            source_type: Optional file type hint (e.g., 'pdf', 'docx').
                        If None, type is auto-detected from file extension or content.

        Returns:
            Converted markdown content as string.

        Raises:
            ConversionError: If conversion fails.
            UnsupportedFormatError: If file format is not supported.
            InvalidInputError: If source is invalid or cannot be read.
        """
        ...

    async def convert_batch(
        self,
        sources: list[Path | bytes],
        source_types: list[str | None] | None = None,
    ) -> list[str]:
        """Convert multiple files to markdown in batch.

        Args:
            sources: List of file paths or raw file bytes.
            source_types: Optional list of type hints for each source.
                         If None, types are auto-detected.

        Returns:
            List of converted markdown content strings.

        Raises:
            ConversionError: If any conversion fails.
            UnsupportedFormatError: If any file format is not supported.
            InvalidInputError: If any source is invalid.
            ValueError: If sources and source_types lists have different lengths.
        """
        ...

    async def supported_formats(self) -> list[str]:
        """Get list of supported file formats.

        Returns:
            List of supported file extensions (e.g., ['pdf', 'docx', 'pptx']).
        """
        ...
