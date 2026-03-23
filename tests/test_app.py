import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original = {
        k: {**v, "participants": v["participants"].copy()}
        for k, v in activities.items()
    }
    yield
    # Restore original state
    for k, v in activities.items():
        v["participants"] = original[k]["participants"].copy()


class TestGetActivities:
    def test_get_all_activities(self, reset_activities):
        """Test retrieving all activities"""
        # Arrange: no setup needed, activities already exist

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data

    def test_activity_structure(self, reset_activities):
        """Test that activities have correct structure"""
        # Arrange: no setup needed

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    def test_signup_success(self, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        email = "success@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds participant to list"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert email in activities[activity_name]["participants"]

    def test_duplicate_signup_rejected(self, reset_activities):
        """Test that duplicate signups are rejected"""
        # Arrange
        email = "duplicate@mergington.edu"
        activity_name = "Chess Club"

        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert - First signup succeeds
        assert response1.status_code == 200

        # Act - Attempt duplicate signup
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert - Duplicate signup fails
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, reset_activities):
        """Test signup for non-existent activity"""
        # Arrange
        email = "test@mergington.edu"
        activity_name = "Fake Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_missing_email(self, reset_activities):
        """Test signup without email parameter"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity_name}/signup")

        # Assert
        assert response.status_code == 422  # Unprocessable Entity


class TestUnregister:
    def test_unregister_success(self, reset_activities):
        """Test successful unregister from activity"""
        # Arrange
        email = "unregister_test@mergington.edu"
        activity_name = "Chess Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister actually removes participant from list"""
        # Arrange
        email = "remove_test@mergington.edu"
        activity_name = "Chess Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        initial_count = len(activities[activity_name]["participants"])

        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={email}")

        # Assert
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_activity(self, reset_activities):
        """Test unregister from non-existent activity"""
        # Arrange
        email = "test@mergington.edu"
        activity_name = "Fake Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404

    def test_unregister_student_not_signed_up(self, reset_activities):
        """Test unregister for student who never signed up"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_twice_fails(self, reset_activities):
        """Test that unregistering twice fails on second attempt"""
        # Arrange
        email = "double_unregister@mergington.edu"
        activity_name = "Chess Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Act - First unregister
        response1 = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert - First unregister succeeds
        assert response1.status_code == 200

        # Act - Attempt second unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert - Second unregister fails
        assert response2.status_code == 400


class TestRootEndpoint:
    def test_root_redirect(self):
        """Test that root redirects to static index"""
        # Arrange: no setup needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
