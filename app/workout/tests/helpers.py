from django.contrib.auth import get_user_model

from core.models import Exercise, Workout, WorkoutExercise


def create_user(**params):
    """Create and return a new user."""
    defaults = {
        "email": "user@example.com",
        "password": "testpass123",
    }
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_workout(user, **params):
    """Create and return a sample workout."""
    defaults = {
        "title": "Sample workout",
        "duration_minutes": 22,
        "description": "Sample workout description.",
        "image": None,
    }
    defaults.update(params)

    return Workout.objects.create(user=user, **defaults)


def create_exercise(user, **params):
    """Create and return a sample exercise."""
    defaults = {"name": "Sample exercise"}
    defaults.update(params)

    return Exercise.objects.create(user=user, **defaults)


def create_workout_exercise(workout, exercise, **params):
    """Create and return a sample workout exercise."""
    defaults = {
        "order": 1,
        "sets": 3,
        "reps": 10,
        "rest_seconds": 60,
    }
    defaults.update(params)

    return WorkoutExercise.objects.create(workout=workout, exercise=exercise, **defaults)
