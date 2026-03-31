from django.urls import path, include

from rest_framework.routers import DefaultRouter

from workout import views


router = DefaultRouter()
router.register("workouts", views.WorkoutViewSet)
router.register("workout-tags", views.WorkoutTagViewSet)
router.register("exercises", views.ExerciseViewSet)
router.register("exercise-tags", views.ExerciseTagViewSet)

app_name = "workout"

urlpatterns = [
    path("", include(router.urls)),
]
