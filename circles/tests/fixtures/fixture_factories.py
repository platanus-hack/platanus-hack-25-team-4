"""
Factory functions for creating test data for all 10 ETL data types.

These factories generate sample data for testing processors, adapters,
and the full ETL pipeline for each data type.
"""

import json
from pathlib import Path
from typing import Any, Dict


class DataTypeFixtures:
    """Factory for creating test fixtures for all 10 data types."""

    @staticmethod
    def create_resume_data() -> Dict[str, Any]:
        """Create sample resume data."""
        return {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "location": "San Francisco, CA",
            "summary": "Experienced software engineer with 5+ years in full-stack development",
            "experience": [
                {
                    "company": "Tech Corp",
                    "position": "Senior Software Engineer",
                    "duration": "2020-2024",
                    "description": "Led development of microservices",
                }
            ],
            "education": [
                {
                    "institution": "University of California",
                    "degree": "B.S. Computer Science",
                    "year": 2018,
                }
            ],
            "skills": ["Python", "JavaScript", "React", "PostgreSQL", "Docker", "AWS"],
        }

    @staticmethod
    def create_photo_metadata() -> Dict[str, Any]:
        """Create sample photo metadata."""
        return {
            "file_name": "photo_001.jpg",
            "file_size": 2500000,  # 2.5 MB
            "mime_type": "image/jpeg",
            "width": 4000,
            "height": 3000,
            "capture_date": "2024-01-15T14:30:00Z",
            "camera": {"make": "Canon", "model": "EOS R5", "lens": "RF 24-70mm f/2.8"},
            "location": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "address": "San Francisco, CA",
            },
            "tags": ["portrait", "professional", "headshot"],
            "analysis": {"people_detected": 1, "quality_score": 0.92},
        }

    @staticmethod
    def create_voice_note_metadata() -> Dict[str, Any]:
        """Create sample voice note metadata."""
        return {
            "file_name": "voice_note_001.wav",
            "file_size": 1200000,  # 1.2 MB
            "mime_type": "audio/wav",
            "duration_seconds": 45.3,
            "sample_rate": 44100,
            "channels": 1,
            "bit_depth": 16,
            "recorded_date": "2024-01-15T10:00:00Z",
            "language": "en",
            "transcription": "Quick reminder to update the documentation and send the proposal",
            "confidence": 0.97,
            "speaker": "John Doe",
        }

    @staticmethod
    def create_calendar_data() -> Dict[str, Any]:
        """Create sample calendar data."""
        return {
            "calendar_owner": "john@example.com",
            "total_events": 3,
            "events": [
                {
                    "title": "Team Standup",
                    "start": "2024-01-15T09:00:00Z",
                    "end": "2024-01-15T09:30:00Z",
                    "location": "Conference Room A",
                    "attendees": ["john@example.com", "jane@example.com"],
                    "recurring": "daily",
                },
                {
                    "title": "Project Review",
                    "start": "2024-01-15T14:00:00Z",
                    "end": "2024-01-15T15:30:00Z",
                    "location": "Virtual - Zoom",
                    "attendees": ["manager@example.com"],
                    "recurring": "monthly",
                },
            ],
        }

    @staticmethod
    def create_screenshot_metadata() -> Dict[str, Any]:
        """Create sample screenshot metadata."""
        return {
            "file_name": "screenshot_001.png",
            "file_size": 800000,
            "mime_type": "image/png",
            "width": 1920,
            "height": 1080,
            "capture_date": "2024-01-15T10:30:00Z",
            "application": "Chrome",
            "url": "https://example.com/dashboard",
            "analysis": {
                "ui_elements": ["button", "text_field", "dropdown"],
                "text_detected": ["Dashboard", "Analytics", "Settings"],
                "layout_type": "web_app",
            },
        }

    @staticmethod
    def create_shared_image_metadata() -> Dict[str, Any]:
        """Create sample shared image metadata."""
        return {
            "file_name": "shared_image_001.jpg",
            "file_size": 3500000,
            "mime_type": "image/jpeg",
            "width": 3840,
            "height": 2160,
            "shared_date": "2024-01-15T11:00:00Z",
            "platform": "Slack",
            "channel": "#design",
            "shared_by": "jane@example.com",
            "caption": "New UI mockup for the dashboard",
            "analysis": {
                "objects": ["mockup", "design", "layout"],
                "mood": "professional",
            },
        }

    @staticmethod
    def create_chat_transcript_data() -> Dict[str, Any]:
        """Create sample chat transcript data."""
        return {
            "platform": "Slack",
            "channel": "engineering",
            "date_range": {
                "start": "2024-01-15T10:00:00Z",
                "end": "2024-01-15T12:00:00Z",
            },
            "total_messages": 15,
            "participants": ["john@example.com", "jane@example.com", "bob@example.com"],
            "messages": [
                {
                    "author": "john@example.com",
                    "text": "Hey team, can we review the PR?",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "reactions": {"thumbsup": 3},
                },
                {
                    "author": "jane@example.com",
                    "text": "Just reviewed it! Looks good.",
                    "timestamp": "2024-01-15T10:45:00Z",
                    "reactions": {},
                },
            ],
        }

    @staticmethod
    def create_email_data() -> Dict[str, Any]:
        """Create sample email data."""
        return {
            "from": "john@example.com",
            "to": ["team@example.com"],
            "cc": ["manager@example.com"],
            "subject": "Project Update - Q1 2024",
            "date": "2024-01-15T10:30:00Z",
            "body": "Team, here's our Q1 progress update...",
            "priority": "high",
            "attachments": [
                {
                    "name": "Q1_Report.pdf",
                    "size": 2500000,
                    "mime_type": "application/pdf",
                }
            ],
        }

    @staticmethod
    def create_social_post_data() -> Dict[str, Any]:
        """Create sample social post data."""
        return {
            "platform": "LinkedIn",
            "author": "John Doe",
            "content": "Excited to announce that our team shipped a major feature!",
            "timestamp": "2024-01-15T09:00:00Z",
            "engagement": {"likes": 127, "comments": 18, "shares": 5},
            "media": [{"type": "image", "url": "https://example.com/image.jpg"}],
            "tags": ["engineering", "innovation"],
        }

    @staticmethod
    def create_blog_post_data() -> Dict[str, Any]:
        """Create sample blog post data."""
        return {
            "title": "Building Scalable Microservices",
            "author": "John Doe",
            "published_at": "2024-01-10T08:00:00Z",
            "slug": "building-scalable-microservices",
            "content": "In this article, we explore the best practices...",
            "excerpt": "A comprehensive guide to designing microservices",
            "word_count": 2500,
            "reading_time_minutes": 12,
            "tags": ["microservices", "architecture", "backend"],
            "category": "Technology",
            "engagement": {"views": 5430, "comments": 23, "shares": 89},
        }

    @staticmethod
    def get_all_fixtures() -> Dict[str, Dict[str, Any]]:
        """Get all fixtures for all 10 data types."""
        return {
            "resume": DataTypeFixtures.create_resume_data(),
            "photo": DataTypeFixtures.create_photo_metadata(),
            "voice_note": DataTypeFixtures.create_voice_note_metadata(),
            "calendar": DataTypeFixtures.create_calendar_data(),
            "screenshot": DataTypeFixtures.create_screenshot_metadata(),
            "shared_image": DataTypeFixtures.create_shared_image_metadata(),
            "chat_transcript": DataTypeFixtures.create_chat_transcript_data(),
            "email": DataTypeFixtures.create_email_data(),
            "social_post": DataTypeFixtures.create_social_post_data(),
            "blog_post": DataTypeFixtures.create_blog_post_data(),
        }


# Convenience functions for creating test data
def create_test_file(file_type: str, content: str, output_path: Path) -> Path:
    """Create a test file with the given content."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    return output_path


def load_fixture_json(fixture_name: str) -> Dict[str, Any]:
    """Load a fixture JSON file."""
    fixture_path = Path(__file__).parent / f"{fixture_name}.json"
    if fixture_path.exists():
        with open(fixture_path) as f:
            return json.load(f)
    return {}


def load_mock_response(response_type: str, size_category: str) -> Dict[str, Any]:
    """Load a mock API response."""
    mock_dir = Path(__file__).parent / "mock_responses"
    response_file = mock_dir / f"{response_type}_responses.json"

    if response_file.exists():
        with open(response_file) as f:
            responses = json.load(f)
            return responses.get(size_category, {})
    return {}
