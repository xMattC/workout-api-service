import tempfile

from PIL import Image
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Exercise, Workout, WorkoutExercise
from workout.serializers import ExerciseSerializer
from workout.tests.helpers import create_user, create_workout, create_exercise, create_workout_exercise
from workout.tests.urls import EXERCISES_LIST_URL, exercise_detail_url, exercise_image_upload_url

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

    def test_user_can_not_create_a_public_exercise(self):
        """Ensure a normal user cannot create a public exercise."""
        payload = {"name": "Bench Press", "is_public": True}
        res = self.client.post(EXERCISES_LIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Exercise.objects.count(), 0)
        self.assertIn("error_is_public", res.data)

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

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
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


class ImageUploadTests(TestCase):
    """Test exercise image upload functionality."""

    def setUp(self):
        """Set up authenticated client and sample exercise."""
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="password123")
        self.client.force_authenticate(self.user)
        self.exercise = create_exercise(user=self.user)

    def tearDown(self):
        """Clean up uploaded image files after each test."""
        if self.exercise.image_1:
            self.exercise.image_1.delete(save=False)
        if self.exercise.image_2:
            self.exercise.image_2.delete(save=False)

    # -----------------------------------------------------------------
    # SINGLE IMAGE UPLOAD
    # -----------------------------------------------------------------

    def test_upload_image_1(self):
        """Ensure image_1 can be uploaded."""
        url = exercise_image_upload_url(self.exercise.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)

            payload = {"image_1": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.exercise.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image_1", res.data)
        self.assertTrue(self.exercise.image_1)

    def test_upload_image_2(self):
        """Ensure image_2 can be uploaded."""
        url = exercise_image_upload_url(self.exercise.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)

            payload = {"image_2": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.exercise.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image_2", res.data)
        self.assertTrue(self.exercise.image_2)

    # -----------------------------------------------------------------
    # BOTH IMAGES UPLOAD
    # -----------------------------------------------------------------

    def test_upload_both_images(self):
        """Ensure both images can be uploaded in one request."""
        url = exercise_image_upload_url(self.exercise.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as img1, tempfile.NamedTemporaryFile(suffix=".jpg") as img2:

            image1 = Image.new("RGB", (10, 10))
            image1.save(img1, format="JPEG")
            img1.seek(0)

            image2 = Image.new("RGB", (10, 10))
            image2.save(img2, format="JPEG")
            img2.seek(0)

            payload = {
                "image_1": img1,
                "image_2": img2,
            }
            res = self.client.post(url, payload, format="multipart")

        self.exercise.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.exercise.image_1)
        self.assertTrue(self.exercise.image_2)

    # -----------------------------------------------------------------
    # INVALID INPUT
    # -----------------------------------------------------------------

    def test_upload_image_bad_request(self):
        """Verify invalid image upload returns 400."""
        url = exercise_image_upload_url(self.exercise.id)

        payload = {"image_1": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
