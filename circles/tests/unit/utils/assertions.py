"""
Shared test assertions and utilities for processor tests.

This module provides reusable assertion functions to reduce duplication
across processor unit tests.
"""

from typing import Any, Dict, List


def assert_processor_result_structure(result: Any) -> None:
    """
    Assert that a processor result has the correct structure.

    Verifies that the result is a SimpleProcessorResult instance with:
    - content attribute (dict)
    - metadata attribute (dict)
    - embeddings attribute

    Args:
        result: The processor result to validate
    """
    assert hasattr(result, "content"), "Result should have 'content' attribute"
    assert hasattr(result, "metadata"), "Result should have 'metadata' attribute"
    assert hasattr(result, "embeddings"), "Result should have 'embeddings' attribute"

    assert isinstance(result.content, dict), "Result.content should be a dict"
    assert isinstance(result.metadata, dict), "Result.metadata should be a dict"


def assert_file_metadata(
    metadata: Dict[str, Any],
    expected_file_type: str,
    min_file_size: int = 0,
) -> None:
    """
    Assert that file metadata has expected structure and values.

    Args:
        metadata: The metadata dict to validate
        expected_file_type: Expected file extension (e.g., ".txt", ".jpg")
        min_file_size: Minimum expected file size in bytes (default: 0)
    """
    assert "file_type" in metadata, "Metadata should contain 'file_type'"
    assert "file_size" in metadata, "Metadata should contain 'file_size'"

    assert metadata["file_type"] == expected_file_type, (
        f"Expected file_type '{expected_file_type}', got '{metadata['file_type']}'"
    )
    assert metadata["file_size"] >= min_file_size, (
        f"Expected file_size >= {min_file_size}, got {metadata['file_size']}"
    )


def assert_content_keys(content: Dict[str, Any], required_keys: List[str]) -> None:
    """
    Assert that content dict contains all required keys.

    Args:
        content: The content dict to validate
        required_keys: List of keys that must be present
    """
    for key in required_keys:
        assert key in content, (
            f"Content should contain key '{key}'. "
            f"Available keys: {list(content.keys())}"
        )


def assert_list_field(
    data: Dict[str, Any],
    field_name: str,
    expected_type: type = list,
) -> None:
    """
    Assert that a field exists and is of the expected type.

    Args:
        data: The dict to check
        field_name: The field name to validate
        expected_type: Expected type for the field (default: list)
    """
    assert field_name in data, f"'{field_name}' should be present in data"
    assert isinstance(data[field_name], expected_type), (
        f"'{field_name}' should be {expected_type.__name__}, "
        f"got {type(data[field_name]).__name__}"
    )


def assert_dict_field(
    data: Dict[str, Any],
    field_name: str,
) -> None:
    """
    Assert that a field exists and is a dict.

    Args:
        data: The dict to check
        field_name: The field name to validate
    """
    assert_list_field(data, field_name, dict)


def assert_file_metadata_with_exif(
    metadata: Dict[str, Any],
    expected_file_type: str,
) -> None:
    """
    Assert file metadata with EXIF data field (for photo processor).

    Args:
        metadata: The metadata dict to validate
        expected_file_type: Expected file extension (e.g., ".jpg")
    """
    assert_file_metadata(metadata, expected_file_type)
    assert "exif_data" in metadata, "Metadata should contain 'exif_data'"
    assert isinstance(metadata["exif_data"], dict), "exif_data should be a dict"


def assert_processor_result_empty_content(
    result: Any, expected_empty_field: str
) -> None:
    """
    Assert that processor result has empty content for a specific field.

    Args:
        result: The processor result to validate
        expected_empty_field: Field name that should be empty (e.g., "full_text")
    """
    assert_processor_result_structure(result)
    assert result.content[expected_empty_field] == "", (
        f"Expected empty {expected_empty_field}, "
        f"got {result.content[expected_empty_field]}"
    )


def assert_media_type(media_type: str, expected_prefix: str = "image/") -> None:
    """
    Assert that media type matches expected pattern.

    Args:
        media_type: The media type string to validate
        expected_prefix: Expected prefix (default: "image/" for photos)
    """
    assert media_type.startswith(expected_prefix), (
        f"Expected media type starting with '{expected_prefix}', got '{media_type}'"
    )


def assert_json_analysis_structure(
    analysis: Dict[str, Any],
) -> None:
    """
    Assert that analysis dict has expected JSON structure.

    Args:
        analysis: The analysis dict from Claude Vision API response
    """
    assert isinstance(analysis, dict), "Analysis should be a dict"
    # Analysis can be empty or contain various fields depending on image content


def assert_caption_content(caption: str, must_not_be_empty: bool = True) -> None:
    """
    Assert that caption has expected content.

    Args:
        caption: The caption string to validate
        must_not_be_empty: Whether caption should not be empty (default: True)
    """
    assert isinstance(caption, str), "Caption should be a string"
    if must_not_be_empty:
        assert len(caption) > 0, "Caption should not be empty"


def assert_transcript_split_structure(
    split: Dict[str, Any],
) -> None:
    """
    Assert that a transcript split has expected structure.

    Args:
        split: A message split from ChatTranscriptProcessor
    """
    required_keys = [
        "chunk_index",
        "chunk_message_count",
        "chunk_start_idx",
        "chunk_end_idx",
    ]
    assert_content_keys(split, required_keys)


def assert_conversation_analysis_structure(
    analysis: Dict[str, Any],
) -> None:
    """
    Assert that conversation analysis has expected structure.

    Args:
        analysis: Analysis dict from ChatTranscriptProcessor
    """
    if analysis:  # Analysis can be empty for empty conversations
        required_keys = [
            "total_messages",
            "unique_participants",
            "participant_activity",
        ]
        assert_content_keys(analysis, required_keys)


def assert_participant_list(participants: List[str]) -> None:
    """
    Assert that participant list is valid.

    Args:
        participants: List of participant names
    """
    assert isinstance(participants, list), "Participants should be a list"
    for participant in participants:
        assert isinstance(participant, str), (
            f"Each participant should be a string, got {type(participant)}"
        )
