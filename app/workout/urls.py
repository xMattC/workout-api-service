from django.urls import path, include

from rest_framework.routers import DefaultRouter

from workout import views


router = DefaultRouter()
router.register("workouts", views.WorkoutViewSet)
router.register("workouts-tags", views.WorkoutTagViewSet, basename="workout-tags")
router.register("exercises", views.ExerciseViewSet)
router.register("exercises-tags", views.ExerciseTagViewSet, basename="exercise-tags")

app_name = "workout"

urlpatterns = [
    path("", include(router.urls)),
]
