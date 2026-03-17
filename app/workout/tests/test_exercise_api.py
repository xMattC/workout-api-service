from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Exercise

from workout.serializers import ExerciseSerializer


EXERCISES_URL = reverse("workout:exercise-list")


def detail_url(exercise_id):
    """Create and return an exercise detail URL."""
    return reverse("workout:exercise-detail", args=[exercise_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicExercisesApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving exercises."""
        res = self.client.get(EXERCISES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateExercisesApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_exercises(self):
        """Test retrieving a list of exercises."""
        Exercise.objects.create(user=self.user, name="Bench Press")
        Exercise.objects.create(user=self.user, name="Squats")

        res = self.client.get(EXERCISES_URL)

        exercises = Exercise.objects.all().order_by("-name")
        serializer = ExerciseSerializer(exercises, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_exercises_limited_to_user(self):
        """Test list of exercises is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Exercise.objects.create(user=user2, name="Salt")
        exercise = Exercise.objects.create(user=self.user, name="Deadlift")

        res = self.client.get(EXERCISES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], exercise.name)
        self.assertEqual(res.data[0]["id"], exercise.id)

    def test_update_exercise(self):
        """Test updating an exercise."""
        exercise = Exercise.objects.create(user=self.user, name="Push Ups")

        payload = {"name": "Bench Press"}
        url = detail_url(exercise.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        exercise.refresh_from_db()
        self.assertEqual(exercise.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Exercise.objects.create(user=self.user, name="Lettuce")

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Exercise.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
