from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Workout, Tag

from workout.serializers import TagSerializer


# ---------------------------------------------------------------------
# URLS
# ---------------------------------------------------------------------

TAGS_URL = reverse("workout:tag-list")
WORKOUTS_URL = reverse("workout:workout-list")


def detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse("workout:tag-detail", args=[tag_id])


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def create_user(email="user@example.com", password="testpass123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


# ---------------------------------------------------------------------
# PUBLIC API TESTS
# ---------------------------------------------------------------------

class PublicTagsApiTests(TestCase):
    """Test unauthenticated access to tag endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Ensure authentication is required to access the tag list endpoint."""
        res = self.client.get(TAGS_URL)

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
        Tag.objects.create(user=self.user, name="Legs day")
        Tag.objects.create(user=self.user, name="Upper Body")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(user=self.user).order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Ensure the tag list endpoint returns only tags belonging to the authenticated user."""
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(user=user2, name="HIIT")
        tag = Tag.objects.create(user=self.user, name="Cardio")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Verify that an authenticated user can update the name of their tag."""
        tag = Tag.objects.create(user=self.user, name="Monday Workout")

        payload = {"name": "Tuesday Workout"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Ensure an authenticated user can delete their own tag successfully."""
        tag = Tag.objects.create(user=self.user, name="300 Workout")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    # -----------------------------------------------------------------
    # WORKOUT TAG RELATIONSHIP TESTS
    # -----------------------------------------------------------------

    def test_create_workout_with_new_tags(self):
        """Ensure new tags are created and linked when provided during workout creation."""
        payload = {
            "title": "Monday Workout",
            "duration_minutes": 45,
            "tags": [{"name": "Back"}, {"name": "Biceps"}],
        }
        res = self.client.post(WORKOUTS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        workouts = Workout.objects.filter(user=self.user)
        self.assertEqual(workouts.count(), 1)

        workout = workouts[0]
        self.assertEqual(workout.tags.count(), 2)

        for tag in payload["tags"]:
            exists = workout.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_workout_with_existing_tags(self):
        """Verify that existing tags are reused (not duplicated) when creating a workout."""
        existing_tag = Tag.objects.create(user=self.user, name="Triceps")

        payload = {
            "title": "Monday Workout",
            "duration_minutes": 45,
            "tags": [{"name": "Triceps"}, {"name": "Biceps"}],
        }
        res = self.client.post(WORKOUTS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        workouts = Workout.objects.filter(user=self.user)
        self.assertEqual(workouts.count(), 1)

        workout = workouts[0]
        self.assertEqual(workout.tags.count(), 2)
        self.assertIn(existing_tag, workout.tags.all())

        for tag in payload["tags"]:
            exists = workout.tags.filter(
                name=tag["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)