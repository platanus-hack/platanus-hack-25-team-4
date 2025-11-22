"""
Output Sanitizer - Sanitizes LLM responses before profile construction.

Removes potentially malicious content and ensures data safety.
"""

import html
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """
    Sanitize text from LLM output.

    Removes or escapes potentially malicious content while preserving readability.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # HTML escape to prevent XSS if this data is displayed in web context
    text = html.escape(text)

    # Remove control characters except newline and tab
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t\r")

    # Limit line length to prevent display issues
    lines = text.split("\n")
    lines = [line[:1000] for line in lines]
    text = "\n".join(lines)

    return text.strip()


def sanitize_object(obj: Any) -> Any:
    """
    Recursively sanitize a Python object.

    Args:
        obj: Object to sanitize

    Returns:
        Sanitized object
    """
    if isinstance(obj, str):
        return sanitize_text(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_object(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_object(item) for item in obj]
    elif obj is None or isinstance(obj, (int, float, bool)):
        return obj
    else:
        # For unknown types, convert to string and sanitize
        return sanitize_text(str(obj))


def sanitize_profile_data(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize an entire profile dictionary from LLM output.

    Args:
        profile_data: Profile data from LLM

    Returns:
        Sanitized profile data
    """
    try:
        logger.debug("Sanitizing profile data from LLM output")
        sanitized = sanitize_object(profile_data)
        logger.debug("Profile data sanitization complete")
        return sanitized
    except Exception as e:
        logger.error(f"Error during profile sanitization: {e}")
        raise


def remove_pii_indicators(text: str) -> str:
    """
    Remove or flag potential PII in text.

    This is a basic implementation. In production, use a dedicated PII detection library.

    Args:
        text: Text to process

    Returns:
        Text with PII indicators removed or flagged
    """
    if not text:
        return text

    # Remove email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", text
    )

    # Remove phone numbers
    text = re.sub(
        r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
        "[PHONE]",
        text,
    )

    # Remove social security numbers
    text = re.sub(
        r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b", "[SSN]", text
    )

    # Remove credit card numbers
    text = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CC]", text)

    # Remove URLs
    text = re.sub(r"https?://[^\s]+", "[URL]", text)

    return text
