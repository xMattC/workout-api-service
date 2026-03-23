import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Workout, Tag, Exercise, WorkoutExercise
from workout.serializers import WorkoutSerializer, WorkoutDetailSerializer


# ---------------------------------------------------------------------
# URLS
# ---------------------------------------------------------------------

WORKOUTS_URL = reverse("workout:workout-list")


def detail_url(workout_id):
    """Create and return a workout detail URL."""
    return reverse("workout:workout-detail", args=[workout_id])


def image_upload_url(workout_id):
    """Create and return an image upload URL."""
    return reverse("workout:workout-upload-image", args=[workout_id])


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def create_user(**params):
    """Create and return a new user."""
    user = get_user_model().objects.create_user(**params)
    return user


def create_workout(user, **params):
    """Create and return a sample workout."""
    defaults = {"title": "Sample workout", "duration_minutes": 22}
    defaults.update(params)

    workout = Workout.objects.create(user=user, **defaults)
    return workout


def create_exercise(user, **params):
    """Create and return a sample exercise."""
    defaults = {"name": "Sample exercise"}
    defaults.update(params)

    exercise = Exercise.objects.create(user=user, **defaults)
    return exercise


def create_workout_exercise(workout, exercise, **params):
    """Create and return a sample workout exercise."""
    defaults = {
        "order": 1,
        "sets": 3,
        "reps": 10,
        "rest_seconds": 60,
    }
    defaults.update(params)

    workout_exercise = WorkoutExercise.objects.create(workout=workout, exercise=exercise, **defaults)
    return workout_exercise


# ---------------------------------------------------------------------
# PUBLIC API TESTS
# ---------------------------------------------------------------------


class PublicWorkoutAPITests(TestCase):
    """Test unauthenticated access to workout endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Ensure authentication is required to access the workout list endpoint."""
        res = self.client.get(WORKOUTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------
# PRIVATE API TESTS
# ---------------------------------------------------------------------


class PrivateWorkoutApiTests(TestCase):
    """Test authenticated interactions with the workout API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testpass123")
        self.client.force_authenticate(self.user)

    # -----------------------------------------------------------------
    # BASIC CRUD
    # -----------------------------------------------------------------

    def test_retrieve_workouts(self):
        """Verify that an authenticated user can retrieve a list of their workouts."""
        create_workout(user=self.user)
        res = self.client.get(WORKOUTS_URL)

        workouts = Workout.objects.filter(user=self.user).order_by("-id")
        serializer = WorkoutSerializer(workouts, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_workout_list_limited_to_user(self):
        """Ensure the workout list endpoint returns only workouts belonging to the authenticated user."""
        other_user = create_user(email="user2@example.com", password="test123")
        create_workout(user=other_user)
        workout = create_workout(user=self.user)

        res = self.client.get(WORKOUTS_URL)

        serializer = WorkoutSerializer(workout)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0], serializer.data)

    def test_get_workout_detail(self):
        """Verify that a user can retrieve detailed information for a specific workout."""
        workout = create_workout(user=self.user)

        url = detail_url(workout.id)
        res = self.client.get(url)

        serializer = WorkoutDetailSerializer(workout)
        self.assertEqual(res.data, serializer.data)

    def test_create_workout(self):
        """Ensure a user can successfully create a workout with basic required fields."""
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
        """Verify that a user can partially update a workout without affecting other fields."""
        workout = create_workout(user=self.user, title="Sample workout title")

        payload = {"title": "New workout title"}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        workout.refresh_from_db()
        self.assertEqual(workout.title, payload["title"])
        self.assertEqual(workout.user, self.user)

    def test_full_update(self):
        """Ensure a user can fully update all editable fields of a workout using PUT."""
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
        """Ensure that attempting to change the workout owner is ignored and does not update the user."""
        new_user = create_user(email="user2@example.com", password="test123")
        workout = create_workout(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(workout.id)
        self.client.patch(url, payload)

        workout.refresh_from_db()
        self.assertEqual(workout.user, self.user)

    def test_delete_workout(self):
        """Verify that a user can delete their own workout successfully."""
        workout = create_workout(user=self.user)

        url = detail_url(workout.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workout.objects.filter(id=workout.id).exists())

    def test_workout_other_users_workout_error(self):
        """Ensure a user cannot delete another user's workout (returns 404)."""
        new_user = create_user(email="user2@example.com", password="test123")
        workout = create_workout(user=new_user)

        url = detail_url(workout.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Workout.objects.filter(id=workout.id).exists())

    # -----------------------------------------------------------------
    # TAG RELATIONSHIP TESTS
    # -----------------------------------------------------------------

    def test_create_tag_on_update(self):
        """Verify that new tags are created and assigned when included in a workout update payload."""
        workout = create_workout(user=self.user)

        payload = {"tags": [{"name": "Leg Day"}]}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Leg Day")
        self.assertIn(new_tag, workout.tags.all())

    def test_update_workout_assign_tag(self):
        """Ensure existing tags can be reassigned on update and previous tags are removed."""
        tag_existing = Tag.objects.create(user=self.user, name="Leg Day")
        workout = create_workout(user=self.user)
        workout.tags.add(tag_existing)

        tag_new = Tag.objects.create(user=self.user, name="Back Day")
        payload = {"tags": [{"name": "Back Day"}]}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_new, workout.tags.all())
        self.assertNotIn(tag_existing, workout.tags.all())

    def test_clear_workout_tags(self):
        """Verify that providing an empty tag list removes all tags from the workout."""
        tag = Tag.objects.create(user=self.user, name="Cardio-run")
        workout = create_workout(user=self.user)
        workout.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(workout.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.tags.count(), 0)

    # -----------------------------------------------------------------
    # EXERCISE RELATIONSHIP TESTS
    # -----------------------------------------------------------------

    def test_create_workout_with_workout_exercises(self):
        """Test creating a workout with nested workout_exercises creates related rows."""
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(workout.workout_exercises.count(), 1)
        self.assertEqual(workout.workout_exercises.first().exercise, exercise)

    def test_update_workout_replaces_workout_exercises(self):
        """Test updating a workout replaces existing workout_exercises."""
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.workout_exercises.count(), 1)
        self.assertEqual(workout.workout_exercises.first().exercise, new_exercise)

    def test_clear_workout_exercises(self):
        """Test that sending empty workout_exercises removes all from the workout."""
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.workout_exercises.count(), 0)

    def test_create_workout_invalid_exercise_id(self):
        """Test error returned when assigning a non-existent exercise ID."""
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_workout_without_workout_exercises_keeps_existing(self):
        """Test updating workout without workout_exercises does not remove existing ones."""
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(workout.workout_exercises.count(), 1)

    # -----------------------------------------------------------------
    # WORKOUT FILTERING TESTS
    # -----------------------------------------------------------------

    def test_filter_by_tags(self):
        """Test filitering by ensuring that only workouts associated with any of the specified tag IDs are returned."""
        wo1 = create_workout(user=self.user, title="Monday - Chest and Back")
        tag1 = Tag.objects.create(user=self.user, name="upper body")
        wo1.tags.add(tag1)

        wo2 = create_workout(user=self.user, title="Wednesday - Legs")
        tag2 = Tag.objects.create(user=self.user, name="lower body")
        wo2.tags.add(tag2)

        wo3 = create_workout(user=self.user, title="Friday - Arms and Shoulders")

        params = {"tags": f"{tag1.id},{tag2.id}"}
        res = self.client.get(WORKOUTS_URL, params)

        s1 = WorkoutSerializer(wo1)
        s2 = WorkoutSerializer(wo2)
        s3 = WorkoutSerializer(wo3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_exercise(self):
        """Test filters by ensuring that only workouts that include any of the specified exercise IDs are returned."""
        wo1 = create_workout(user=self.user, title="Monday - Chest and Back")
        ex1 = create_exercise(user=self.user, name="Bench Press")
        create_workout_exercise(workout=wo1, exercise=ex1)

        wo2 = create_workout(user=self.user, title="Wednesday - Legs")
        ex2 = create_exercise(user=self.user, name="Squats")
        create_workout_exercise(workout=wo2, exercise=ex2)

        wo3 = create_workout(user=self.user, title="Friday - Arms and Shoulders")

        params = {"exercises": f"{ex1.id},{ex2.id}"}
        res = self.client.get(WORKOUTS_URL, params)

        s1 = WorkoutSerializer(wo1)
        s2 = WorkoutSerializer(wo2)
        s3 = WorkoutSerializer(wo3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    """Test workout image upload functionality."""

    def setUp(self):
        """Set up authenticated client and sample workout."""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("user@example.com", "password123")
        self.client.force_authenticate(self.user)
        self.workout = create_workout(user=self.user)

    def tearDown(self):
        """Clean up uploaded image files after each test."""
        self.workout.image.delete()

    def test_upload_image(self):
        """Ensure a valid image can be uploaded and stored for a workout."""
        url = image_upload_url(self.workout.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)

            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.workout.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.workout.image.path))

    def test_upload_image_bad_request(self):
        """Verify that uploading invalid image data returns a 400 error."""
        url = image_upload_url(self.workout.id)

        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
