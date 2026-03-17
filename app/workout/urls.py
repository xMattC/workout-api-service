from django.urls import path, include

from rest_framework.routers import DefaultRouter

from workout import views


router = DefaultRouter()
router.register("workouts", views.WorkoutViewSet)
router.register("tags", views.TagViewSet)


app_name = "workout"

urlpatterns = [
    path("", include(router.urls)),
]
