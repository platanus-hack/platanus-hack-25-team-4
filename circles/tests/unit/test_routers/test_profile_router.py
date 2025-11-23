"""
Unit tests for profile management API endpoints.

Tests the profile router endpoints for creating, updating, and retrieving
user bio and interests.
"""

import pytest
from fastapi.testclient import TestClient
from src.etl.main import app
from src.profile_schema import Interest, UserProfile


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.mark.unit
class TestProfileEndpoints:
    """Test profile management endpoints."""

    def test_create_profile_with_bio_and_interests(self, client, db_session):
        """Test creating a new profile with bio and interests."""
        # Arrange
        request_data = {
            "user_id": "test_user_001",
            "bio": "Software engineer passionate about building innovative products",
            "interests": [
                {
                    "title": "Web Development",
                    "description": "Building scalable web applications with modern frameworks",
                },
                {
                    "title": "Machine Learning",
                    "description": "Exploring ML applications in product development",
                },
            ],
        }

        # Act
        response = client.post(
            "/api/v1/profile/update-bio-interests", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_001"
        assert data["bio"] == request_data["bio"]
        assert len(data["interests"]) == 2
        assert data["interests"][0]["title"] == "Web Development"
        assert data["profile_completed"] is True
        assert data["message"] == "Profile created successfully"

    def test_create_profile_with_bio_only(self, client, db_session):
        """Test creating a profile with only bio (no interests)."""
        # Arrange
        request_data = {
            "user_id": "test_user_002",
            "bio": "Tech enthusiast and lifelong learner",
        }

        # Act
        response = client.post(
            "/api/v1/profile/update-bio-interests", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_002"
        assert data["bio"] == request_data["bio"]
        assert data["interests"] is None
        assert data["profile_completed"] is False
        assert data["message"] == "Profile created successfully"

    def test_create_profile_with_interests_only(self, client, db_session):
        """Test creating a profile with only interests (no bio)."""
        # Arrange
        request_data = {
            "user_id": "test_user_003",
            "interests": [
                {
                    "title": "Photography",
                    "description": "Landscape and street photography",
                }
            ],
        }

        # Act
        response = client.post(
            "/api/v1/profile/update-bio-interests", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_003"
        assert data["bio"] is None
        assert len(data["interests"]) == 1
        assert data["profile_completed"] is False
        assert data["message"] == "Profile created successfully"

    def test_update_existing_profile(self, client, db_session):
        """Test updating an existing profile's bio and interests."""
        # Arrange - Create initial profile
        initial_profile = UserProfile(
            user_id="test_user_004",
            bio="Initial bio",
            interests=[Interest(title="Old Interest", description="Old description")],
        )
        db_session.add(initial_profile)
        db_session.commit()

        # Act - Update the profile
        update_data = {
            "user_id": "test_user_004",
            "bio": "Updated bio with new information",
            "interests": [
                {"title": "New Interest", "description": "New description"},
                {"title": "Another Interest", "description": "Another description"},
            ],
        }
        response = client.post("/api/v1/profile/update-bio-interests", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_004"
        assert data["bio"] == "Updated bio with new information"
        assert len(data["interests"]) == 2
        assert data["interests"][0]["title"] == "New Interest"
        assert data["profile_completed"] is True
        assert data["message"] == "Profile updated successfully"

    def test_update_profile_bio_only(self, client, db_session):
        """Test updating only the bio of an existing profile."""
        # Arrange - Create initial profile
        initial_profile = UserProfile(
            user_id="test_user_005",
            bio="Old bio",
            interests=[Interest(title="Coding", description="Python development")],
        )
        db_session.add(initial_profile)
        db_session.commit()

        # Act - Update only bio
        update_data = {"user_id": "test_user_005", "bio": "New bio"}
        response = client.post("/api/v1/profile/update-bio-interests", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "New bio"
        # Interests should remain unchanged
        assert len(data["interests"]) == 1
        assert data["interests"][0]["title"] == "Coding"

    def test_get_profile_success(self, client, db_session):
        """Test retrieving an existing profile."""
        # Arrange
        profile = UserProfile(
            user_id="test_user_006",
            bio="My bio",
            interests=[
                Interest(title="Reading", description="Fiction and non-fiction")
            ],
        )
        db_session.add(profile)
        db_session.commit()

        # Act
        response = client.get("/api/v1/profile/test_user_006")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_006"
        assert data["bio"] == "My bio"
        assert len(data["interests"]) == 1
        assert data["message"] == "Profile retrieved successfully"

    def test_get_profile_not_found(self, client, db_session):
        """Test retrieving a profile that doesn't exist."""
        # Act
        response = client.get("/api/v1/profile/nonexistent_user")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"].lower()

    def test_create_profile_empty_interests_list(self, client, db_session):
        """Test creating a profile with an empty interests list."""
        # Arrange
        request_data = {"user_id": "test_user_007", "bio": "Test bio", "interests": []}

        # Act
        response = client.post(
            "/api/v1/profile/update-bio-interests", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_007"
        assert data["bio"] == "Test bio"
        assert data["interests"] == []
        # Empty list should not count as having interests
        assert data["profile_completed"] is False

    def test_create_profile_with_multiple_interests(self, client, db_session):
        """Test creating a profile with many interests."""
        # Arrange
        interests = [
            {"title": f"Interest {i}", "description": f"Description {i}"}
            for i in range(5)
        ]
        request_data = {
            "user_id": "test_user_008",
            "bio": "Curious person with many interests",
            "interests": interests,
        }

        # Act
        response = client.post(
            "/api/v1/profile/update-bio-interests", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["interests"]) == 5
        assert data["profile_completed"] is True

    def test_profile_timestamps(self, client, db_session):
        """Test that created_at and updated_at timestamps are set correctly."""
        # Arrange & Act
        request_data = {
            "user_id": "test_user_009",
            "bio": "Test bio",
            "interests": [{"title": "Test", "description": "Test interest"}],
        }
        response = client.post(
            "/api/v1/profile/update-bio-interests", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data
        # For new profiles, created_at and updated_at should be close
        from datetime import datetime

        created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        updated = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        time_diff = abs((updated - created).total_seconds())
        assert time_diff < 2  # Should be within 2 seconds

    def test_update_profile_updates_timestamp(self, client, db_session):
        """Test that updating a profile updates the updated_at timestamp."""
        # Arrange - Create initial profile
        initial_profile = UserProfile(
            user_id="test_user_010",
            bio="Initial bio",
        )
        db_session.add(initial_profile)
        db_session.commit()
        db_session.refresh(initial_profile)
        initial_updated_at = initial_profile.updated_at

        # Wait a bit to ensure timestamp difference
        import time

        time.sleep(0.1)

        # Act - Update the profile
        update_data = {"user_id": "test_user_010", "bio": "Updated bio"}
        response = client.post("/api/v1/profile/update-bio-interests", json=update_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        from datetime import datetime

        final_updated_at = datetime.fromisoformat(
            data["updated_at"].replace("Z", "+00:00")
        )
        assert final_updated_at > initial_updated_at
