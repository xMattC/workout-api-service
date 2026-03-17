from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Workout, Tag

from workout.serializers import WorkoutSerializer, WorkoutDetailSerializer


WORKOUTS_URL = reverse("workout:workout-list")


def create_workout(user, **params):
    """Create and return a sample workout."""
    defaults = {"title": "Sample workout", "duration_minutes": 22}
    defaults.update(params)

    workout = Workout.objects.create(user=user, **defaults)
    return workout


def detail_url(workout_id):
    """Create and return a workout detail URL."""
    return reverse("workout:workout-detail", args=[workout_id])


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicWorkoutAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(WORKOUTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateWorkoutApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("user@example.com", "testpass123")
        self.client.force_authenticate(self.user)

    def test_retrieve_workouts(self):
        """Test retrieving a list of workouts."""
        create_workout(user=self.user)
        create_workout(user=self.user)

        res = self.client.get(WORKOUTS_URL)

        workouts = Workout.objects.all().order_by("-id")
        serializer = WorkoutSerializer(workouts, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_workout_list_limited_to_user(self):
        """Test list of workouts is limited to authenticated user."""
        other_user = create_user(email="user2@example.com", password="test123")
        create_workout(user=other_user)
        workout = create_workout(user=self.user)

        res = self.client.get(WORKOUTS_URL)

        serializer = WorkoutSerializer(workout)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0], serializer.data)

    def test_get_workout_detail(self):
        """Test get workout detail."""
        workout = create_workout(user=self.user)

        url = detail_url(workout.id)
        res = self.client.get(url)

        serializer = WorkoutDetailSerializer(workout)
        self.assertEqual(res.data, serializer.data)

    def test_create_workout(self):
        """Test creating a workout."""
        payload = {
            "title": "Sample workout",
            "duration_minutes": 30,
        }
        res = self.client.post(WORKOUTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        workout = Workout.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(workout, key))

    def test_partial_update(self):
        """Test partial update of a workout."""
        workout = create_workout(
            user=self.user,
            title="Sample workout title",
        )

        payload = {"title": "New workout title"}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        workout.refresh_from_db()
        self.assertEqual(workout.title, payload["title"])
        self.assertEqual(workout.user, self.user)

    def test_full_update(self):
        """Test full update of workout."""
        workout = create_workout(
            user=self.user,
            title="Sample workout title",
            description="Sample workout description.",
        )

        payload = {
            "title": "New workout title",
            "description": "New workout description",
            "duration_minutes": 10,
        }
        url = detail_url(workout.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        workout.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(workout, k), v)
        self.assertEqual(workout.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the workout user results in an error."""
        new_user = create_user(email="user2@example.com", password="test123")
        workout = create_workout(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(workout.id)
        self.client.patch(url, payload)

        workout.refresh_from_db()
        self.assertEqual(workout.user, self.user)

    def test_delete_workout(self):
        """Test deleting a workout successful."""
        workout = create_workout(user=self.user)

        url = detail_url(workout.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workout.objects.filter(id=workout.id).exists())

    def test_workout_other_users_workout_error(self):
        """Test trying to delete another users workout gives error."""
        new_user = create_user(email="user2@example.com", password="test123")
        workout = create_workout(user=new_user)

        url = detail_url(workout.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Workout.objects.filter(id=workout.id).exists())

    def test_create_tag_on_update(self):
        """Test create tag when updating a workout."""
        workout = create_workout(user=self.user)

        payload = {"tags": [{"name": "Leg Day"}]}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Leg Day")
        self.assertIn(new_tag, workout.tags.all())

    def test_update_workout_assign_tag(self):
        """Test assigning an existing tag when updating a workout."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Leg Day")
        workout = create_workout(user=self.user)
        workout.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Back Day")
        payload = {"tags": [{"name": "Back Day"}]}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, workout.tags.all())
        self.assertNotIn(tag_breakfast, workout.tags.all())

    def test_clear_workout_tags(self):
        """Test clearing a workouts tags."""
        tag = Tag.objects.create(user=self.user, name="Cardio-run")
        workout = create_workout(user=self.user)
        workout.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.tags.count(), 0)
