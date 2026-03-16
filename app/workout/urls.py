from django.urls import path, include

from rest_framework.routers import DefaultRouter

from workout import views


router = DefaultRouter()
router.register("workouts", views.WorkoutViewSet)

app_name = "workout"

urlpatterns = [
    path("", include(router.urls)),
]
