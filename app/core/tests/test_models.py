from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core import models


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test core model behaviour."""

    def test_create_user_with_email_successful(self):
        """Ensure a user can be created with an email and password."""
        email = "test@example.com"
        password = "testpass123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Verify that email addresses are normalized when creating users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Ensure creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self):
        """Verify that a superuser is created with correct permissions."""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "test123",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_workout(self):
        """Ensure a workout is created successfully and string representation returns its title."""
        user = create_user()

        workout = models.Workout.objects.create(
            user=user,
            title="Sample workout name",
            duration_minutes=60,
        )

        self.assertEqual(str(workout), workout.title)

    def test_create_workout_exercise(self):
        """Verify workout exercise is created and string representation is correct."""
        user = create_user()

        workout = models.Workout.objects.create(
            user=user,
            title="Sample workout",
            duration_minutes=60,
        )

        exercise = models.Exercise.objects.create(
            user=user,
            name="Push-up",
        )

        workout_exercise = models.WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            order=1,
            sets=3,
            reps=10,
            rest_seconds=60,
        )

        expected_str = f"{workout.title} - {exercise.name} (1)"

        self.assertEqual(str(workout_exercise), expected_str)

    def test_create_exercise_tag(self):
        """Verify that a tag is created successfully and string representation returns its name."""
        user = create_user()

        tag = models.ExerciseTag.objects.create(user=user, name="Tag_name", type="tag_type")

        self.assertEqual(str(tag), tag.name)
        self.assertEqual("tag_type", tag.type)

    def test_create_workout_tag(self):
        """Verify that a tag is created successfully and string representation returns its name."""
        user = create_user()

        tag = models.WorkoutTag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)

    def test_create_exercise(self):
        """Ensure an exercise is created successfully and string representation returns its name."""
        user = create_user()
        exercise = models.Exercise.objects.create(user=user, name="Exercise1")

        self.assertFalse(exercise.is_public)
        self.assertEqual(str(exercise), exercise.name)

    @patch("uuid.uuid4")
    def test_exercise_file_name_uuid(self, mock_uuid):
        """Ensure exercise image file path is generated using a UUID-based filename."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid

        file_path = models.exercise_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/exercise/{uuid}.jpg")
