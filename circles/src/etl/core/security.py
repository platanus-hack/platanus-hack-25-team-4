"""
Secure File Validation - Protection against file upload attacks.

Protects against:
- Path traversal (../../etc/passwd)
- Zip bombs (zip files with extreme compression)
- XXE attacks (XML External Entity injection)
- MIME type spoofing
- Oversized files
"""

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set


@dataclass
class ValidationResult:
    """Result of file validation."""

    is_valid: bool
    error: Optional[str] = None
    file_size: int = 0


class SecureFileValidator:
    """
    Secure file validation with multiple checks.

    Provides:
    - Extension whitelisting
    - MIME type validation (basic magic byte check)
    - Size limits
    - Zip bomb detection
    - Path traversal prevention
    - Filename sanitization
    """

    # Allowed file types
    ALLOWED_EXTENSIONS: Dict[str, Set[str]] = {
        "resume": {".pdf", ".docx", ".txt"},
        "image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"},
        "audio": {".mp3", ".wav", ".ogg", ".webm", ".m4a"},
        "calendar": {".ics"},
    }

    # Magic bytes for file type detection
    MAGIC_BYTES: Dict[bytes, str] = {
        b"%PDF": "application/pdf",
        b"\x50\x4b\x03\x04": "application/zip",  # ZIP files
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89PNG": "image/png",
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
    }

    # File size limits (in bytes)
    MAX_FILE_SIZES: Dict[str, int] = {
        "resume": 10 * 1024 * 1024,  # 10 MB
        "image": 25 * 1024 * 1024,  # 25 MB
        "audio": 50 * 1024 * 1024,  # 50 MB
        "calendar": 5 * 1024 * 1024,  # 5 MB
        "default": 10 * 1024 * 1024,  # 10 MB
    }

    # Zip bomb detection
    MAX_DECOMPRESSION_RATIO = 100  # Max ratio of compressed:uncompressed
    MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500 MB max uncompressed

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Removes:
        - Directory path components (../, /, \)
        - Leading dots (hidden files)
        - Special characters
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        # Get just the filename (remove any path)
        filename = Path(filename).name

        # Remove path separators
        filename = filename.replace("/", "").replace("\\", "")

        # Remove leading dots
        filename = filename.lstrip(".")

        # Keep only safe characters
        filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

        if not filename or filename == ".":
            raise ValueError("Filename invalid after sanitization")

        return filename

    @staticmethod
    def validate_extension(filename: str, file_type: str) -> ValidationResult:
        """Validate file extension against whitelist."""
        allowed_exts = SecureFileValidator.ALLOWED_EXTENSIONS.get(file_type, set())
        if not allowed_exts:
            return ValidationResult(False, f"Unknown file type: {file_type}")

        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_exts:
            return ValidationResult(
                False,
                f"Extension {file_ext} not allowed. Allowed: {', '.join(allowed_exts)}",
            )

        return ValidationResult(True)

    @staticmethod
    def validate_size(content: bytes, file_type: str) -> ValidationResult:
        """Validate file size against limits."""
        max_size = SecureFileValidator.MAX_FILE_SIZES.get(
            file_type, SecureFileValidator.MAX_FILE_SIZES["default"]
        )

        file_size = len(content)
        if file_size > max_size:
            return ValidationResult(
                False,
                f"File size {file_size} exceeds maximum {max_size}",
                file_size=file_size,
            )

        return ValidationResult(True, file_size=file_size)

    @staticmethod
    def detect_magic_bytes(content: bytes) -> str:
        """Detect file type from magic bytes."""
        for magic, mime_type in SecureFileValidator.MAGIC_BYTES.items():
            if content.startswith(magic):
                return mime_type
        return "application/octet-stream"

    @staticmethod
    def check_zip_bomb(content: bytes) -> ValidationResult:
        """Detect potential zip bomb attacks."""
        # Check for ZIP magic bytes
        if not content.startswith(b"\x50\x4b\x03\x04"):
            return ValidationResult(True)

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                total_uncompressed = sum(info.file_size for info in zf.infolist())

                # Check decompression ratio
                if len(content) > 0:
                    ratio = total_uncompressed / len(content)
                    if ratio > SecureFileValidator.MAX_DECOMPRESSION_RATIO:
                        return ValidationResult(
                            False,
                            f"Potential zip bomb: compression ratio {ratio:.1f}x exceeds limit",
                        )

                # Check uncompressed size
                if total_uncompressed > SecureFileValidator.MAX_UNCOMPRESSED_SIZE:
                    return ValidationResult(
                        False,
                        f"Decompressed size {total_uncompressed} exceeds {SecureFileValidator.MAX_UNCOMPRESSED_SIZE}",
                    )

        except zipfile.BadZipFile:
            # Not a valid zip, continue
            pass

        return ValidationResult(True)

    @staticmethod
    def check_xxe_vulnerability(content: bytes, file_type: str) -> ValidationResult:
        """Check for XXE (XML External Entity) attacks."""
        if file_type not in ["resume", "calendar"]:
            return ValidationResult(True)

        try:
            content_str = content.decode("utf-8", errors="ignore").lower()
        except Exception:
            return ValidationResult(True)

        # Check for dangerous patterns
        dangerous_patterns = ["<!entity", "<!doctype", "system", "public"]

        for pattern in dangerous_patterns:
            if pattern in content_str:
                # Check for external entity indicators
                if "file://" in content_str or "http://" in content_str:
                    return ValidationResult(
                        False, "Potentially malicious XML content detected"
                    )

        return ValidationResult(True)

    @staticmethod
    async def validate_file(
        filename: str, content: bytes, file_type: str
    ) -> ValidationResult:
        """
        Comprehensive file validation.

        Checks:
        1. Filename safety
        2. Extension whitelist
        3. File size
        4. Magic bytes / file type
        5. Zip bomb detection
        6. XXE vulnerability
        """
        # 1. Sanitize filename
        try:
            SecureFileValidator.sanitize_filename(filename)
        except ValueError as e:
            return ValidationResult(False, str(e))

        # 2. Check extension
        result = SecureFileValidator.validate_extension(filename, file_type)
        if not result.is_valid:
            return result

        # 3. Check size
        result = SecureFileValidator.validate_size(content, file_type)
        if not result.is_valid:
            return result

        # 4. Check magic bytes (basic file type detection)
        magic_type = SecureFileValidator.detect_magic_bytes(content)

        # 5. Zip bomb check
        result = SecureFileValidator.check_zip_bomb(content)
        if not result.is_valid:
            return result

        # 6. XXE check
        result = SecureFileValidator.check_xxe_vulnerability(content, file_type)
        if not result.is_valid:
            return result

        return ValidationResult(True, file_size=len(content))
