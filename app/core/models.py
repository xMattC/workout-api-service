import logging
import os
import uuid

from django.conf import settings
from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,  # Provides password hashing and authentication features
    BaseUserManager,  # Provides helper methods for creating users
    PermissionsMixin,  # Adds permission-related fields (groups, is_superuser, etc.)
)


logger = logging.getLogger(__name__)


def exercise_image_file_path(instance, filename):
    """Generate file path for new exercise image."""
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"

    return os.path.join("uploads", "exercise", filename)


def workout_image_file_path(instance, filename):
    """Compatibility wrapper for old migrations."""
    return exercise_image_file_path(instance, filename)


class UserManager(BaseUserManager):
    """Custom manager for the User model.

    The manager defines how User objects are created. Django calls these methods when creating users via code,
    management commands, or tests.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user.

        The email address is required and used as the login identifier.
        The password is hashed using Django's built-in password system before being stored in the database.
        """
        if not email:
            raise ValueError("User must have an email address.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        logger.info("User created id=%s email=%s", user.id, user.email)

        return user

    def create_superuser(self, email, password):
        """Create and return a superuser.

        A superuser has full administrative permissions and access to the Django admin interface.
        """
        user = self.create_user(email, password)

        # Grant admin site access and full permissions
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        logger.info("Superuser created id=%s email=%s", user.id, user.email)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for the project.

    This replaces Django's default username-based user model with an email-based authentication system.
    """

    email = models.EmailField(max_length=255, unique=True)  # Primary login identifier
    name = models.CharField(max_length=255)  # Display name for the user
    is_active = models.BooleanField(default=True)  # Determines whether the account is active
    is_staff = models.BooleanField(default=False)  # Allows access to the Django admin interface
    objects = UserManager()  # Attach the custom manager to the model
    USERNAME_FIELD = "email"  # Attach the custom manager to the model


class Workout(models.Model):
    """Entity model - Workout object."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workouts")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.IntegerField()  # TODO: Temporary field — later derived from WorkoutExercise
    wo_tags = models.ManyToManyField("WorkoutTag", blank=True, related_name="workouts")

    def __str__(self):
        return self.title


class WorkoutTag(models.Model):
    """Entity model - Tag for filtering workouts."""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workout_tags")

    def __str__(self):
        return self.name


class WorkoutExercise(models.Model):
    """Join model - A single exercise entry inside a workout."""

    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="workout_exercises")
    exercise = models.ForeignKey("Exercise", on_delete=models.CASCADE, related_name="workout_exercises")
    order = models.PositiveIntegerField()
    sets = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    rest_seconds = models.PositiveIntegerField()
    user_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.workout.title} - {self.exercise.name} ({self.order})"


class Exercise(models.Model):
    """Exercise model representing a workout movement."""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exercises")
    image_1 = models.ImageField(null=True, blank=True, upload_to=exercise_image_file_path)
    image_2 = models.ImageField(null=True, blank=True, upload_to=exercise_image_file_path)
    is_public = models.BooleanField(default=False)

    DIFFICULTY_BEGINNER = "beginner"
    DIFFICULTY_INTERMEDIATE = "intermediate"
    DIFFICULTY_ADVANCED = "advanced"
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, "Beginner"),
        (DIFFICULTY_INTERMEDIATE, "Intermediate"),
        (DIFFICULTY_ADVANCED, "Advanced"),
    ]
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_BEGINNER)

    ex_tags = models.ManyToManyField("ExerciseTag", blank=True, related_name="exercises")

    def __str__(self):
        return self.name


class ExerciseTag(models.Model):
    """Tag model used to classify and filter exercises."""

    TYPE_EQUIPMENT = "equipment"  # E.g. "Dumbbell", "Barbell", "Kettlebell", "Bodyweight"
    TYPE_CATEGORY = "category"  # E.g. "Strength", "Cardio", "olympic weightlifting", "Mobility"
    PRIMARY_MUSCLE = "primary_muscle"  # E.g. "Quadriceps"
    SECONDARY_MUSCLE = "secondary_muscle"  # E.g. "calves", "glutes", "hamstrings""

    TAG_TYPE_CHOICES = [
        (TYPE_EQUIPMENT, "Equipment"),
        (TYPE_CATEGORY, "Category"),
        (PRIMARY_MUSCLE, "Primary Muscle"),
        (SECONDARY_MUSCLE, "Secondary Muscle"),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TAG_TYPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="exercise_tags",
    )
    is_system = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "name", "type")

    def __str__(self):
        return f"{self.name} ({self.type})"
