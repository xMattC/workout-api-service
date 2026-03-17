from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Workout, Tag

from workout.serializers import TagSerializer


TAGS_URL = reverse("workout:tag-list")
WORKOUTS_URL = reverse("workout:workout-list")

def detail_url(tag_id):
    """Create and return a tag detail url."""
    return reverse("workout:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name="Legs day")
        Tag.objects.create(user=self.user, name="Upper Body")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Tag.objects.create(user=user2, name="HIIT")
        tag = Tag.objects.create(user=self.user, name="Cardio")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating a tag."""
        tag = Tag.objects.create(user=self.user, name="Monday Workout")

        payload = {"name": "Tusday Workout"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name="300 Workout")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())



    def test_create_workout_with_new_tags(self):
        """Test creating a workout with new tags."""
        payload = {
            'title': 'Monday Workout',
            'duration_minutes': 45,
            'tags': [{'name': 'Back'}, {'name': 'Biceps'}],
        }
        res = self.client.post(WORKOUTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        workouts = Workout.objects.filter(user=self.user)
        self.assertEqual(workouts.count(), 1)
        workout = workouts[0]
        self.assertEqual(workout.tags.count(), 2)
        for tag in payload['tags']:
            exists = workout.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_workout_with_existing_tags(self):
        """Test creating a workout with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Monday Workout',
            'duration_minutes': 45,
            'tags': [{'name': 'Back'}, {'name': 'Biceps'}],
        }
        res = self.client.post(WORKOUTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        workouts = Workout.objects.filter(user=self.user)
        self.assertEqual(workouts.count(), 1)
        workout = workouts[0]
        self.assertEqual(workout.tags.count(), 2)
        self.assertIn(tag_indian, workout.tags.all())
        for tag in payload['tags']:
            exists = workout.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)