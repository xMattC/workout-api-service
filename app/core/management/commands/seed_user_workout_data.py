import csv
import re

from django.core.management.base import BaseCommand
from django.conf import settings
from core import models
from django.contrib.auth import get_user_model


def slugify(value):
    """Convert exercise name into image filename slug.

    Normalises text into lowercase hyphenated format used for image naming.
    """
    text = str(value).strip().lower()
    text = text.replace("_", "-")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def clean_tag_name(value):
    """Normalise a tag name.

    Trims whitespace, collapses repeated spaces, and title-cases the result.
    Returns an empty string if the value is blank.
    """
    if not value:
        return ""

    value = re.sub(r"\s+", " ", str(value).strip())
    return value.title()


def split_csv_list(value):
    """Split a multi-value CSV field into clean individual values.

    Supports values separated by "|" or ",".

    Returns:
    - A list of cleaned non-empty strings.
    """
    if not value:
        return []

    parts = re.split(r"\s*\|\s*|\s*,\s*", str(value).strip())
    return [clean_tag_name(item) for item in parts if clean_tag_name(item)]


class Command(BaseCommand):
    help = "Seed database from user workout CSV"

    def handle(self, *args, **kwargs):

        # ---------------------------------------------------------------------
        # GET OR CREATE SYSTEM USER
        # ---------------------------------------------------------------------
        Example_User = get_user_model()
        example_user, created = Example_User.objects.get_or_create(
            email="api_demo@workoutapp.com", defaults={"is_staff": False, "is_superuser": False}
        )
        if created:
            example_user.set_unusable_password()
            example_user.save()

        # ---------------------------------------------------------------------
        # LOAD CSV FILE
        # ---------------------------------------------------------------------
        workout_csv_path = settings.BASE_DIR / "data" / "example_user_workouts.csv"
        exercise_csv_path = settings.BASE_DIR / "data" / "example_user_workout_exercises.csv"

        with open(workout_csv_path, newline="", encoding="utf-8") as workout_file:
            workout_reader = csv.DictReader(workout_file)

            for row in workout_reader:

                day = row["day"].strip()
                title = row["title"].strip()
                description = row["description"].strip()
                duration_minutes = int(row["duration_minutes"].strip())
                tags = split_csv_list(row.get("tags", ""))

                # -----------------------------------------------------------------
                workout, _ = models.Workout.objects.update_or_create(
                    user=example_user,
                    title=title,
                    defaults={
                        "description": description,
                        "duration_minutes": duration_minutes,
                    },
                )

                # -----------------------------------------------------------------
                for tag in tags:
                    wo_tag, _ = models.WorkoutTag.objects.get_or_create(name=tag, user=example_user)
                    workout.wo_tags.add(wo_tag)

                with open(exercise_csv_path, newline="", encoding="utf-8") as exercise_file:
                    exercise_reader = csv.DictReader(exercise_file)

                    for row in exercise_reader:
                        if row["day"].strip() == day:
                            name = row["exercise_name"].strip()
                            order = int(row["order"].strip())
                            sets = int(row["sets"].strip())
                            reps = int(row["reps"].strip())
                            rest_seconds = int(row["rest_seconds"].strip())
                            usr_notes = row["user_notes"].strip()

                            exercise = models.Exercise.objects.filter(name=name).first()

                            if not exercise:
                                continue

                            workout_exercise, created = models.WorkoutExercise.objects.update_or_create(
                                workout=workout,
                                order=order,
                                defaults={
                                    "exercise": exercise,
                                    "sets": sets,
                                    "reps": reps,
                                    "rest_seconds": rest_seconds,
                                    "user_notes": usr_notes,
                                },
                            )

                            workout_exercise.save()
