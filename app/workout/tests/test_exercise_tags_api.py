from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Exercise, ExerciseTag
from workout.serializers import ExerciseTagSerializer
from workout.tests.helpers import create_user
from workout.tests.urls import EXERCISE_TAGS_LIST_URL, EXERCISES_LIST_URL, exercise_tag_detail_url


# ---------------------------------------------------------------------
# PUBLIC API TESTS
# ---------------------------------------------------------------------


class PublicExerciseTagsApiTests(TestCase):
    """Test unauthenticated access to exercise tag endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Ensure authentication is required to access the exercise tag list endpoint."""
        res = self.client.get(EXERCISE_TAGS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------
# PRIVATE API TESTS
# ---------------------------------------------------------------------


class PrivateExerciseTagsApiTests(TestCase):
    """Test authenticated interactions with the exercise tag API."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    # -----------------------------------------------------------------
    # BASIC CRUD
    # -----------------------------------------------------------------

    def test_retrieve_exercise_tags(self):
        """Verify that an authenticated user can retrieve their custom exercise tags."""
        tag1 = ExerciseTag.objects.create(
            user=self.user,
            name="Chest",
            type=ExerciseTag.PRIMARY_MUSCLE,
        )
        tag2 = ExerciseTag.objects.create(
            user=self.user,
            name="Dumbbell",
            type=ExerciseTag.TYPE_EQUIPMENT,
        )

        res = self.client.get(EXERCISE_TAGS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in res.data]
        self.assertIn(tag1.id, returned_ids)
        self.assertIn(tag2.id, returned_ids)

    def test_create_exercise_tag(self):
        """Verify that an authenticated user can create a custom exercise tag."""
        payload = {
            "name": "Strength",
            "type": ExerciseTag.TYPE_CATEGORY,
        }

        res = self.client.post(EXERCISE_TAGS_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        tag = ExerciseTag.objects.get(id=res.data["id"])
        self.assertEqual(tag.user, self.user)
        self.assertEqual(tag.name, payload["name"])
        self.assertEqual(tag.type, payload["type"])
        self.assertFalse(tag.is_system)

    def test_update_exercise_tag(self):
        """Verify that an authenticated user can update their own custom exercise tag."""
        tag = ExerciseTag.objects.create(
            user=self.user,
            name="Biceps",
            type=ExerciseTag.PRIMARY_MUSCLE,
        )

        payload = {"name": "Triceps"}
        url = exercise_tag_detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])
        self.assertEqual(tag.type, ExerciseTag.PRIMARY_MUSCLE)

    def test_delete_exercise_tag(self):
        """Ensure an authenticated user can delete their own custom exercise tag."""
        tag = ExerciseTag.objects.create(
            user=self.user,
            name="Mobility",
            type=ExerciseTag.TYPE_CATEGORY,
        )

        url = exercise_tag_detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ExerciseTag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_exercises(self):
        """Test listing exercise tags limited to those assigned to exercises."""
        tag1 = ExerciseTag.objects.create(
            user=self.user,
            name="Quadriceps",
            type=ExerciseTag.PRIMARY_MUSCLE,
        )
        tag2 = ExerciseTag.objects.create(
            user=self.user,
            name="Kettlebell",
            type=ExerciseTag.TYPE_EQUIPMENT,
        )
        exercise = Exercise.objects.create(
            name="Goblet Squat",
            user=self.user,
        )
        exercise.ex_tags.add(tag1)

        res = self.client.get(EXERCISE_TAGS_LIST_URL, {"assigned_only": 1})

        s1 = ExerciseTagSerializer(tag1)
        s2 = ExerciseTagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered exercise tags returns a unique list."""
        tag = ExerciseTag.objects.create(
            user=self.user,
            name="Bodyweight",
            type=ExerciseTag.TYPE_EQUIPMENT,
        )
        ExerciseTag.objects.create(
            user=self.user,
            name="Cardio",
            type=ExerciseTag.TYPE_CATEGORY,
        )

        exercise1 = Exercise.objects.create(name="Push Up", user=self.user)
        exercise2 = Exercise.objects.create(name="Pull Up", user=self.user)

        exercise1.ex_tags.add(tag)
        exercise2.ex_tags.add(tag)

        res = self.client.get(EXERCISE_TAGS_LIST_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)

    # -----------------------------------------------------------------
    # EXTRA TESTS
    # -----------------------------------------------------------------

    def test_system_tags_visible_to_authenticated_user(self):
        """Ensure system exercise tags are included in the list response."""
        system_tag = ExerciseTag.objects.create(
            name="Barbell",
            type=ExerciseTag.TYPE_EQUIPMENT,
            is_system=True,
        )
        user_tag = ExerciseTag.objects.create(
            user=self.user,
            name="Hamstrings",
            type=ExerciseTag.SECONDARY_MUSCLE,
        )

        res = self.client.get(EXERCISE_TAGS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in res.data]

        self.assertIn(system_tag.id, returned_ids)
        self.assertIn(user_tag.id, returned_ids)

    def test_tags_limited_to_user_and_system_only(self):
        """Ensure only system tags and the authenticated user's custom tags are returned."""
        other_user = create_user(email="other@example.com")

        own_tag = ExerciseTag.objects.create(
            user=self.user,
            name="Glutes",
            type=ExerciseTag.PRIMARY_MUSCLE,
        )
        other_tag = ExerciseTag.objects.create(
            user=other_user,
            name="Calves",
            type=ExerciseTag.SECONDARY_MUSCLE,
        )
        system_tag = ExerciseTag.objects.create(
            name="Bodyweight",
            type=ExerciseTag.TYPE_EQUIPMENT,
            is_system=True,
        )

        res = self.client.get(EXERCISE_TAGS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_ids = [item["id"] for item in res.data]

        self.assertIn(own_tag.id, returned_ids)
        self.assertIn(system_tag.id, returned_ids)
        self.assertNotIn(other_tag.id, returned_ids)

    def test_user_cannot_update_system_exercise_tag(self):
        """Ensure a user cannot update a system exercise tag."""
        tag = ExerciseTag.objects.create(
            name="Strength",
            type=ExerciseTag.TYPE_CATEGORY,
            is_system=True,
        )

        payload = {"name": "Powerlifting"}
        url = exercise_tag_detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        tag.refresh_from_db()
        self.assertEqual(tag.name, "Strength")

    def test_user_cannot_delete_system_exercise_tag(self):
        """Ensure a user cannot delete a system exercise tag."""
        tag = ExerciseTag.objects.create(
            name="Dumbbell",
            type=ExerciseTag.TYPE_EQUIPMENT,
            is_system=True,
        )

        url = exercise_tag_detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(ExerciseTag.objects.filter(id=tag.id).exists())

    def test_user_cannot_retrieve_other_users_custom_tag(self):
        """Ensure a user cannot retrieve another user's custom exercise tag."""
        other_user = create_user(email="other@example.com")
        tag = ExerciseTag.objects.create(
            user=other_user,
            name="Calves",
            type=ExerciseTag.SECONDARY_MUSCLE,
        )

        url = exercise_tag_detail_url(tag.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_other_users_custom_tag(self):
        """Ensure a user cannot update another user's custom exercise tag."""
        other_user = create_user(email="other@example.com")
        tag = ExerciseTag.objects.create(
            user=other_user,
            name="Calves",
            type=ExerciseTag.SECONDARY_MUSCLE,
        )
        payload = {"name": "Glutes"}
        url = exercise_tag_detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        tag.refresh_from_db()
        self.assertEqual(tag.name, "Calves")

    def test_user_cannot_delete_other_users_custom_tag(self):
        """Ensure a user cannot delete another user's custom exercise tag."""
        other_user = create_user(email="other@example.com")
        tag = ExerciseTag.objects.create(
            user=other_user,
            name="Calves",
            type=ExerciseTag.SECONDARY_MUSCLE,
        )

        url = exercise_tag_detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(ExerciseTag.objects.filter(id=tag.id).exists())

    # -----------------------------------------------------------------
    # EXERCISE TAG RELATIONSHIP TESTS
    # -----------------------------------------------------------------

    def test_create_exercise_with_new_tags(self):
        """Ensure new exercise tags are created and linked when provided during exercise creation."""
        payload = {
            "name": "Bench Press",
            "difficulty": "beginner",
            "ex_tags": [
                {"name": "Chest", "type": ExerciseTag.PRIMARY_MUSCLE},
                {"name": "Strength", "type": ExerciseTag.TYPE_CATEGORY},
            ],
        }

        res = self.client.post(EXERCISES_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        exercises = Exercise.objects.filter(user=self.user)
        self.assertEqual(exercises.count(), 1)

        exercise = exercises[0]
        self.assertEqual(exercise.ex_tags.count(), 2)

        for tag in payload["ex_tags"]:
            exists = exercise.ex_tags.filter(
                name=tag["name"],
                type=tag["type"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_exercise_with_existing_tags(self):
        """Verify that existing exercise tags are reused when creating an exercise."""
        existing_tag = ExerciseTag.objects.create(
            user=self.user,
            name="Chest",
            type=ExerciseTag.PRIMARY_MUSCLE,
        )

        payload = {
            "name": "Incline Bench Press",
            "difficulty": "intermediate",
            "ex_tags": [
                {"name": "Chest", "type": ExerciseTag.PRIMARY_MUSCLE},
                {"name": "Strength", "type": ExerciseTag.TYPE_CATEGORY},
            ],
        }

        res = self.client.post(EXERCISES_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        exercises = Exercise.objects.filter(user=self.user)
        self.assertEqual(exercises.count(), 1)

        exercise = exercises[0]
        self.assertEqual(exercise.ex_tags.count(), 2)
        self.assertIn(existing_tag, exercise.ex_tags.all())

        for tag in payload["ex_tags"]:
            exists = exercise.ex_tags.filter(
                name=tag["name"],
                type=tag["type"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
