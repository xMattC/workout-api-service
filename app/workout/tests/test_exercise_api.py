from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Exercise, Workout, WorkoutExercise
from workout.serializers import ExerciseSerializer
from workout.tests.helpers import create_user, create_workout, create_workout_exercise
from workout.tests.urls import EXERCISES_LIST_URL, exercise_detail_url

# ---------------------------------------------------------------------
# PUBLIC API TESTS
# ---------------------------------------------------------------------


class PublicExercisesApiTests(TestCase):
    """Test unauthenticated access to exercise endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Ensure authentication is required to access the exercise list endpoint."""
        res = self.client.get(EXERCISES_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------
# PRIVATE API TESTS
# ---------------------------------------------------------------------


class PrivateExercisesApiTests(TestCase):
    """Test authenticated interactions with the exercise API."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    # -----------------------------------------------------------------
    # BASIC CRUD
    # -----------------------------------------------------------------

    def test_admin_can_create_public_exercise(self):
        """Ensure an admin user can create a public exercise."""
        admin_user = create_user(email="admin@example.com", is_staff=True)
        self.client.force_authenticate(admin_user)

        payload = {
            "name": "Bench Press",
            "is_public": True,
        }

        res = self.client.post(EXERCISES_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        exercise = Exercise.objects.get(id=res.data["id"])
        self.assertEqual(exercise.user, admin_user)
        self.assertTrue(exercise.is_public)

    def test_admin_can_create_private_exercise(self):
        """Ensure admin can also create private exercises if needed."""
        admin_user = create_user(email="admin@example.com", is_staff=True)
        self.client.force_authenticate(admin_user)

        payload = {
            "name": "Custom Move",
            "is_public": False,
        }

        res = self.client.post(EXERCISES_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        exercise = Exercise.objects.get(id=res.data["id"])
        self.assertFalse(exercise.is_public)

    def test_retrieve_exercises(self):
        """Verify that an authenticated user can retrieve their own exercises and public exercises."""
        admin_user = create_user(email="admin@example.com", is_staff=True)

        Exercise.objects.create(user=self.user, name="Bench Press", is_public=False)
        Exercise.objects.create(user=self.user, name="Squats", is_public=False)
        Exercise.objects.create(user=admin_user, name="Push Up", is_public=True)

        res = self.client.get(EXERCISES_LIST_URL)

        exercises = (
            Exercise.objects.filter(user=self.user).union(Exercise.objects.filter(is_public=True)).order_by("-name")
        )
        serializer = ExerciseSerializer(exercises, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_exercise_always_private(self):
        """Ensure a normal user creates exercises as private, even if is_public is sent."""
        payload = {"name": "Bench Press", "is_public": True}
        res = self.client.post(EXERCISES_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        exercise = Exercise.objects.get(id=res.data["id"])
        self.assertEqual(exercise.user, self.user)
        self.assertFalse(exercise.is_public)

    def test_retrieve_exercises_includes_user_private_and_public(self):
        """Ensure the exercise list includes the user's private exercises and public exercises."""
        admin_user = create_user(email="admin@example.com", is_staff=True)
        other_user = create_user(email="other@example.com")

        private_own = Exercise.objects.create(user=self.user, name="My Deadlift", is_public=False)
        public_admin = Exercise.objects.create(user=admin_user, name="Push Up", is_public=True)
        private_other = Exercise.objects.create(user=other_user, name="Secret Exercise", is_public=False)

        res = self.client.get(EXERCISES_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        returned_ids = [item["id"] for item in res.data]
        self.assertIn(private_own.id, returned_ids)
        self.assertIn(public_admin.id, returned_ids)
        self.assertNotIn(private_other.id, returned_ids)

    def test_exercises_limited_to_user_and_public_exercises(self):
        """Ensure the exercise list returns the user's own exercises and public exercises only."""
        admin_user = create_user(email="admin@example.com", is_staff=True)
        user2 = create_user(email="user2@example.com")

        private_own = Exercise.objects.create(user=self.user, name="Deadlift", is_public=False)
        private_other = Exercise.objects.create(user=user2, name="Squats", is_public=False)
        public_exercise = Exercise.objects.create(user=admin_user, name="Bench Press", is_public=True)

        res = self.client.get(EXERCISES_LIST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        returned_ids = [item["id"] for item in res.data]
        self.assertIn(private_own.id, returned_ids)
        self.assertIn(public_exercise.id, returned_ids)
        self.assertNotIn(private_other.id, returned_ids)

    def test_update_exercise(self):
        """Verify that an authenticated user can update the name of their exercise."""
        exercise = Exercise.objects.create(user=self.user, name="Push Ups")

        payload = {"name": "Bench Press"}
        url = exercise_detail_url(exercise.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        exercise.refresh_from_db()
        self.assertEqual(exercise.name, payload["name"])

    def test_user_cannot_make_exercise_public(self):
        """Ensure a normal user cannot make their own exercise public."""
        exercise = Exercise.objects.create(user=self.user, name="Push Ups", is_public=False)

        payload = {"is_public": True}
        url = exercise_detail_url(exercise.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        exercise.refresh_from_db()
        self.assertFalse(exercise.is_public)

    def test_delete_exercise(self):
        """Ensure an authenticated user can delete their own exercise successfully."""
        exercise = Exercise.objects.create(user=self.user, name="Sit ups")

        url = exercise_detail_url(exercise.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exercises = Exercise.objects.filter(user=self.user)
        self.assertFalse(exercises.exists())

    def test_filter_exercises_assigned_to_workouts(self):
        """Test listing exercises assigned to workouts only."""
        ex1 = Exercise.objects.create(user=self.user, name="Lunges")
        ex2 = Exercise.objects.create(user=self.user, name="Squats")
        workout = Workout.objects.create(title="Leg Day", duration_minutes=55, user=self.user)

        WorkoutExercise.objects.create(workout=workout, exercise=ex1, order=1, sets=3, reps=10, rest_seconds=60)

        res = self.client.get(EXERCISES_LIST_URL, {"assigned_only": 1})

        s1 = ExerciseSerializer(ex1)
        s2 = ExerciseSerializer(ex2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_assigned_only_returns_unique_exercise(self):
        """Assigned filter returns each exercise once even if linked to multiple workouts."""
        exercise = Exercise.objects.create(user=self.user, name="Squats")
        workout1 = create_workout(user=self.user, title="Upper Body Workout", duration_minutes=45)
        workout2 = create_workout(user=self.user, title="Lower Body Workout", duration_minutes=55)
        create_workout_exercise(workout=workout1, exercise=exercise)
        create_workout_exercise(workout=workout2, exercise=exercise)

        res = self.client.get(EXERCISES_LIST_URL, {"assigned_only": 1})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], exercise.id)
        self.assertEqual(res.data[0]["name"], exercise.name)
