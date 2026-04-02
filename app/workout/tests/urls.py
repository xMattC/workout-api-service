from django.urls import reverse

WORKOUTS_LIST_URL = reverse("workout:workout-list")
EXERCISES_LIST_URL = reverse("workout:exercise-list")
WORKOUT_TAGS_LIST_URL = reverse("workout:workout-tags-list")
EXERCISE_TAGS_LIST_URL = reverse("workout:exercise-tags-list")


def workout_detail_url(workout_id):
    """Return the URL for the workout detail endpoint."""
    return reverse("workout:workout-detail", args=[workout_id])


def exercise_detail_url(exercise_id):
    """Return the URL for the exercise detail endpoint."""
    return reverse("workout:exercise-detail", args=[exercise_id])


def workout_tag_detail_url(tag_id):
    """Return the URL for the tag detail endpoint."""
    return reverse("workout:workout-tags-detail", args=[tag_id])


def exercise_tag_detail_url(tag_id):
    """Return the URL for the tag detail endpoint."""
    return reverse("workout:exercise-tags-detail", args=[tag_id])


def exercise_image_upload_url(exercise_id):
    """Return the URL for the exercise image upload endpoint."""
    return reverse("workout:exercise-upload-image", args=[exercise_id])
