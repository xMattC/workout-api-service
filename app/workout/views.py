from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from core.models import Workout, Tag, Exercise
from workout import serializers


class WorkoutViewSet(viewsets.ModelViewSet):
    """View for manage workout APIs."""

    serializer_class = serializers.WorkoutDetailSerializer
    queryset = Workout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve workouts for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "list":
            return serializers.WorkoutSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new workout."""
        serializer.save(user=self.request.user)


class BaseAttrViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base viewset for TagViewSet and ExerciseViewSet."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseAttrViewSet):
    """Manage tags in the database."""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class ExerciseViewSet(BaseAttrViewSet):
    """Manage exercises in the database."""

    serializer_class = serializers.ExerciseSerializer
    queryset = Exercise.objects.all()
