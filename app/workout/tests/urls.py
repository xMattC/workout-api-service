from django.urls import reverse

WORKOUTS_LIST_URL = reverse("workout:workout-list")
EXERCISES_LIST_URL = reverse("workout:exercise-list")
TAGS_LIST_URL = reverse("workout:tag-list")


def workout_detail_url(workout_id):
    """Return the URL for the workout detail endpoint."""
    return reverse("workout:workout-detail", args=[workout_id])


def exercise_detail_url(exercise_id):
    """Return the URL for the exercise detail endpoint."""
    return reverse("workout:exercise-detail", args=[exercise_id])


def tag_detail_url(tag_id):
    """Return the URL for the tag detail endpoint."""
    return reverse("workout:tag-detail", args=[tag_id])


def exercise_image_upload_url(exercise_id):
    """Return the URL for the exercise image upload endpoint."""
    return reverse("workout:exercise-upload-image", args=[exercise_id])
