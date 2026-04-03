from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Workout, WorkoutTag
from workout.serializers import WorkoutTagSerializer
from workout.tests.urls import WORKOUT_TAGS_LIST_URL, WORKOUTS_LIST_URL, workout_tag_detail_url
from workout.tests.helpers import create_user

# ---------------------------------------------------------------------
# PUBLIC API TESTS
# ---------------------------------------------------------------------


class PublicTagsApiTests(TestCase):
    """Test unauthenticated access to tag endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Ensure authentication is required to access the tag list endpoint."""
        res = self.client.get(WORKOUT_TAGS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------
# PRIVATE API TESTS
# ---------------------------------------------------------------------


class PrivateTagsApiTests(TestCase):
    """Test authenticated interactions with the tag API."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    # -----------------------------------------------------------------
    # BASIC CRUD
    # -----------------------------------------------------------------

    def test_retrieve_tags(self):
        """Verify that an authenticated user can retrieve a list of their tags."""
        WorkoutTag.objects.create(user=self.user, name="Legs day")
        WorkoutTag.objects.create(user=self.user, name="Upper Body")

        res = self.client.get(WORKOUT_TAGS_LIST_URL)

        tags = WorkoutTag.objects.filter(user=self.user).order_by("-name")
        serializer = WorkoutTagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_tags_limited_to_user(self):
        """Ensure the tag list endpoint returns only tags belonging to the authenticated user."""
        user2 = create_user(email="user2@example.com")
        WorkoutTag.objects.create(user=user2, name="HIIT")
        tag = WorkoutTag.objects.create(user=self.user, name="Cardio")

        res = self.client.get(WORKOUT_TAGS_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["name"], tag.name)
        self.assertEqual(res.data["results"][0]["id"], tag.id)

    def test_update_workout_tag(self):
        """Verify that an authenticated user can update the name of their tag."""
        tag = WorkoutTag.objects.create(user=self.user, name="Monday Workout")

        payload = {"name": "Tuesday Workout"}
        url = workout_tag_detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_workout_tag(self):
        """Ensure an authenticated user can delete their own tag successfully."""
        tag = WorkoutTag.objects.create(user=self.user, name="300 Workout")

        url = workout_tag_detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = WorkoutTag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_workouts(self):
        """Test listing tags to those assigned to workouts."""
        tag1 = WorkoutTag.objects.create(user=self.user, name="HIIT")
        tag2 = WorkoutTag.objects.create(user=self.user, name="Weight Lifting")
        workout = Workout.objects.create(
            title="Crossfit",
            duration_minutes=60,
            user=self.user,
        )
        workout.wo_tags.add(tag1)

        res = self.client.get(WORKOUT_TAGS_LIST_URL, {"assigned_only": 1})

        s1 = WorkoutTagSerializer(tag1)
        s2 = WorkoutTagSerializer(tag2)
        self.assertIn(s1.data, res.data["results"])
        self.assertNotIn(s2.data, res.data["results"])

    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""
        tag = WorkoutTag.objects.create(user=self.user, name="Beginner program")
        WorkoutTag.objects.create(user=self.user, name="Dinner")
        workout1 = Workout.objects.create(
            title="Full Body Workout",
            duration_minutes=50,
            user=self.user,
        )
        workout2 = Workout.objects.create(
            title="Workout A - 2day split",
            duration_minutes=30,
            user=self.user,
        )
        workout1.wo_tags.add(tag)
        workout2.wo_tags.add(tag)

        res = self.client.get(WORKOUT_TAGS_LIST_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data["results"]), 1)

    # -----------------------------------------------------------------
    # WORKOUT TAG RELATIONSHIP TESTS
    # -----------------------------------------------------------------

    def test_create_workout_with_new_tags(self):
        """Ensure new tags are created and linked when provided during workout creation."""
        payload = {
            "title": "Monday Workout",
            "duration_minutes": 45,
            "wo_tags": [{"name": "Strength"}, {"name": "Upper Body"}],
        }
        res = self.client.post(WORKOUTS_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        workouts = Workout.objects.filter(user=self.user)
        self.assertEqual(workouts.count(), 1)

        workout = workouts[0]
        self.assertEqual(workout.wo_tags.count(), 2)

        for tag in payload["wo_tags"]:
            exists = workout.wo_tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_workout_with_existing_tags(self):
        """Verify that existing tags are reused (not duplicated) when creating a workout."""
        existing_tag = WorkoutTag.objects.create(user=self.user, name="Strength")

        payload = {
            "title": "Monday Workout",
            "duration_minutes": 45,
            "wo_tags": [{"name": "Strength"}, {"name": "Upper Body"}],
        }
        res = self.client.post(WORKOUTS_LIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        workouts = Workout.objects.filter(user=self.user)
        self.assertEqual(workouts.count(), 1)

        workout = workouts[0]
        self.assertEqual(workout.wo_tags.count(), 2)
        self.assertIn(existing_tag, workout.wo_tags.all())

        for tag in payload["wo_tags"]:
            exists = workout.wo_tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_filter_assigned_tags_limited_to_user(self):
        """Ensure "assigned_only=1" only returns assigned tags belonging to the authenticated user."""
        other_user = create_user(email="other@example.com")

        own_tag = WorkoutTag.objects.create(user=self.user, name="Own Assigned Tag")
        other_tag = WorkoutTag.objects.create(user=other_user, name="Other Assigned Tag")

        own_workout = Workout.objects.create(title="Own Workout", duration_minutes=45, user=self.user)
        other_workout = Workout.objects.create(title="Other Workout", duration_minutes=30, user=other_user)

        own_workout.wo_tags.add(own_tag)
        other_workout.wo_tags.add(other_tag)

        res = self.client.get(WORKOUT_TAGS_LIST_URL, {"assigned_only": 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], own_tag.id)
        self.assertEqual(res.data["results"][0]["name"], own_tag.name)
