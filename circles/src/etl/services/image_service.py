"""
Image Service - Handles image optimization for VLM processing.

Provides async image resizing and compression to optimize for
Claude Vision API processing while maintaining quality.
"""

import asyncio
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class ImageService:
    """
    Service for image optimization and processing.

    Handles resizing, compression, and format selection for optimal
    VLM processing with minimal bandwidth and processing time.
    """

    # Claude Vision API optimal dimensions (max 1568px per side)
    MAX_DIMENSION = 1568
    COMPRESSION_QUALITY = 85  # JPEG quality (0-100)

    @staticmethod
    async def resize_image_async(
        input_path: Path, output_path: Path, max_dimension: int = MAX_DIMENSION
    ) -> Path:
        """
        Resize image to optimal dimensions for Claude Vision API.

        Maintains aspect ratio while ensuring both dimensions fit within limit.
        Runs in thread pool to avoid blocking.

        Args:
            input_path: Path to input image
            output_path: Path for resized image
            max_dimension: Maximum dimension (width or height) in pixels

        Returns:
            Path to resized image
        """

        def _resize():
            try:
                from PIL import Image

                with Image.open(input_path) as image:
                    original_format = image.format or "JPEG"

                    # Calculate new dimensions maintaining aspect ratio
                    width, height = image.size
                    if width > max_dimension or height > max_dimension:
                        ratio = min(max_dimension / width, max_dimension / height)
                        new_width = int(width * ratio)
                        new_height = int(height * ratio)

                        logger.info(
                            f"Resizing image: {width}x{height} -> {new_width}x{new_height}"
                        )
                        image = image.resize(
                            (new_width, new_height), Image.Resampling.LANCZOS
                        )
                    else:
                        logger.info(f"Image already optimal size: {width}x{height}")

                    # Save with compression
                    image.save(
                        output_path,
                        format=original_format,
                        quality=ImageService.COMPRESSION_QUALITY,
                        optimize=True,
                    )
                return output_path

            except Exception as e:
                logger.error(f"Failed to resize image: {e}")
                raise

        try:
            result = await asyncio.to_thread(_resize)
            return result
        except Exception as e:
            logger.error(f"Image resizing failed: {e}")
            raise

    @staticmethod
    async def compress_image_async(
        input_path: Path, output_path: Path, quality: int = COMPRESSION_QUALITY
    ) -> Path:
        """
        Compress image while maintaining quality.

        Reduces file size for bandwidth efficiency.
        Runs in thread pool to avoid blocking.

        Args:
            input_path: Path to input image
            output_path: Path for compressed image
            quality: Compression quality (0-100, 85 recommended)

        Returns:
            Path to compressed image
        """

        def _compress():
            try:
                from PIL import Image

                with Image.open(input_path) as image:
                    original_format = image.format or "JPEG"

                    # Get original size
                    original_size = input_path.stat().st_size

                    # Convert RGBA to RGB if needed for JPEG
                    if original_format == "JPEG" and image.mode == "RGBA":
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        background.paste(image, mask=image.split()[3])
                        image = background

                    # Save with compression
                    image.save(
                        output_path,
                        format=original_format,
                        quality=quality,
                        optimize=True,
                    )

                # Log size reduction
                compressed_size = output_path.stat().st_size
                reduction = ((original_size - compressed_size) / original_size) * 100
                logger.info(
                    f"Compressed image: {original_size} -> {compressed_size} bytes ({reduction:.1f}% reduction)"
                )

                return output_path

            except Exception as e:
                logger.error(f"Failed to compress image: {e}")
                raise

        try:
            result = await asyncio.to_thread(_compress)
            return result
        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            raise

    @staticmethod
    async def optimize_image_async(input_path: Path, output_path: Path) -> Path:
        """
        Fully optimize image: resize + compress.

        Combines resizing and compression for maximum efficiency.

        Args:
            input_path: Path to input image
            output_path: Path for optimized image

        Returns:
            Path to optimized image
        """
        try:
            # First resize if needed
            await ImageService.resize_image_async(input_path, output_path)

            # Then compress
            await ImageService.compress_image_async(output_path, output_path)

            return output_path

        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            raise

    @staticmethod
    def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
        """
        Get image dimensions without loading full image.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (width, height)
        """
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.warning(f"Could not get image dimensions: {e}")
            return (0, 0)

    @staticmethod
    def get_file_size_mb(image_path: Path) -> float:
        """
        Get image file size in MB.

        Args:
            image_path: Path to image file

        Returns:
            File size in MB
        """
        return image_path.stat().st_size / (1024 * 1024)

    @staticmethod
    def needs_optimization(
        image_path: Path, max_dimension: int = MAX_DIMENSION
    ) -> bool:
        """
        Check if image needs optimization.

        Args:
            image_path: Path to image file
            max_dimension: Maximum acceptable dimension

        Returns:
            True if optimization recommended
        """
        try:
            width, height = ImageService.get_image_dimensions(image_path)
            size_mb = ImageService.get_file_size_mb(image_path)

            # Recommend optimization if:
            # 1. Dimension exceeds maximum
            # 2. File size > 2MB
            needs_resize = width > max_dimension or height > max_dimension
            needs_compress = size_mb > 2.0

            return needs_resize or needs_compress

        except Exception as e:
            logger.warning(f"Could not assess optimization needs: {e}")
            # Default to optimization if unsure
            return True

    @staticmethod
    async def process_image_for_vlm(input_path: Path) -> Tuple[Path, bool]:
        """
        Process image for VLM input.

        Optimizes image if needed, returns optimized path.
        Original file is preserved.

        Args:
            input_path: Path to original image

        Returns:
            Tuple of (image_path_to_use, was_optimized)
        """
        try:
            # Check if optimization is needed
            if not ImageService.needs_optimization(input_path):
                logger.info(f"Image already optimal: {input_path.name}")
                return input_path, False

            # Create optimized version with _optimized suffix
            output_path = (
                input_path.parent / f"{input_path.stem}_optimized{input_path.suffix}"
            )

            logger.info(f"Optimizing image: {input_path.name}")
            await ImageService.optimize_image_async(input_path, output_path)

            return output_path, True

        except Exception as e:
            logger.warning(f"Image optimization failed, using original: {e}")
            # Fallback to original if optimization fails
            return input_path, False

    @staticmethod
    async def cleanup_optimized_image(image_path: Path, is_optimized: bool) -> None:
        """
        Clean up optimized image file if created.

        Args:
            image_path: Path to optimized image
            is_optimized: Whether this was an optimized version
        """
        if is_optimized and image_path.exists():
            try:
                await asyncio.to_thread(image_path.unlink)
                logger.info(f"Cleaned up optimized image: {image_path.name}")
            except Exception as e:
                logger.warning(f"Failed to clean up optimized image: {e}")
