from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from core.models import Workout
from workout import serializers


class WorkoutViewSet(viewsets.ModelViewSet):
    """View for manage workout APIs."""

    serializer_class = serializers.WorkoutSerializer
    queryset = Workout.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> Workout:
        """Retrieve workouts for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "retrieve":
            return serializers.WorkoutDetailSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new workout."""
        serializer.save(user=self.request.user)
