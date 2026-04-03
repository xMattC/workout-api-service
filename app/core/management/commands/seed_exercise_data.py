import csv
import re
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from core import models
from django.contrib.auth import get_user_model
from django.core.files import File


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
    help = "Seed database from exercises CSV"

    def handle(self, *args, **kwargs):

        # ---------------------------------------------------------------------
        # GET OR CREATE SYSTEM USER
        # ---------------------------------------------------------------------
        System_User = get_user_model()
        system_user, created = System_User.objects.get_or_create(
            email="system_user@workoutapp.com", defaults={"is_staff": True, "is_superuser": True}
        )
        if created:
            system_user.set_unusable_password()
            system_user.save()

        # ---------------------------------------------------------------------
        # LOAD CSV FILE
        # ---------------------------------------------------------------------
        csv_path = settings.BASE_DIR / "data" / "exercises.csv"
        image_dir = settings.BASE_DIR / "data" / "images"
        with open(csv_path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:

                # -----------------------------------------------------------------
                # READ EXERCISE DATA
                # -----------------------------------------------------------------
                name = row["name"].strip()
                difficulty = row["difficulty"].strip()

                equipment = clean_tag_name(row.get("equipment", ""))
                category = clean_tag_name(row.get("category", ""))
                primary_muscles = split_csv_list(row.get("primary_muscles", ""))
                secondary_muscles = split_csv_list(row.get("secondary_muscles", ""))

                # TODO - add instructions field to model and seed from CSV
                # instructions = row.get("instructions", "").strip()

                # -----------------------------------------------------------------
                # CREATE OR GET EXERCISE
                # -----------------------------------------------------------------
                exercise, _ = models.Exercise.objects.update_or_create(
                    name=name,
                    user=system_user,
                    defaults={
                        "is_public": True,
                        "difficulty": difficulty,
                    },
                )

                # -----------------------------------------------------------------
                # UPLAOD IMAGES
                # -----------------------------------------------------------------

                # IMAGE 1
                image_1 = f"{slugify(name)}-1.jpg"
                image_1_path = os.path.join(image_dir, image_1)

                if os.path.exists(image_1_path):
                    with open(image_1_path, "rb") as f:
                        exercise.image_1.save(image_1, File(f), save=False)
                else:
                    self.stdout.write(self.style.WARNING(f"[MISSING] image-1: {image_1_path}"))

                # IMAGE 2
                image_2 = f"{slugify(name)}-2.jpg"
                image_2_path = os.path.join(image_dir, image_2)

                if os.path.exists(image_2_path):
                    with open(image_2_path, "rb") as f:
                        exercise.image_2.save(image_2, File(f), save=False)
                else:
                    self.stdout.write(self.style.WARNING(f"[MISSING] image-2: {image_2_path}"))

                exercise.save()

                # -----------------------------------------------------------------
                # BUILD TAG DEFINITIONS
                # -----------------------------------------------------------------
                tag_definitions = []

                if equipment:
                    tag_definitions.append({"name": equipment, "type": models.ExerciseTag.TYPE_EQUIPMENT})

                if category:
                    tag_definitions.append({"name": category, "type": models.ExerciseTag.TYPE_CATEGORY})

                for muscle in primary_muscles:
                    tag_definitions.append({"name": muscle, "type": models.ExerciseTag.PRIMARY_MUSCLE})

                for muscle in secondary_muscles:
                    tag_definitions.append({"name": muscle, "type": models.ExerciseTag.SECONDARY_MUSCLE})

                # -----------------------------------------------------------------
                # CREATE / GET TAGS AND ATTACH TO EXERCISE
                # -----------------------------------------------------------------
                for tag_data in tag_definitions:
                    tag, _ = models.ExerciseTag.objects.get_or_create(
                        name=tag_data["name"],
                        type=tag_data["type"],
                        user=None,
                        defaults={"is_system": True},
                    )
                    exercise.ex_tags.add(tag)

        self.stdout.write(self.style.SUCCESS("Data successfully seeded!"))
