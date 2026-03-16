from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Workout

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
        other_user = get_user_model().objects.create_user("other@example.com", "password123")
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
