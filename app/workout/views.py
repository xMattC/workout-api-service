from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Workout, Tag, Exercise
from workout import serializers


class WorkoutViewSet(viewsets.ModelViewSet):
    """Manage workout API endpoints. Access is restricted to authenticated users, and all queryset results are limited
    to objects owned by the current user.
    """

    serializer_class = serializers.WorkoutDetailSerializer
    queryset = Workout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return workouts for the authenticated user only. Results are ordered by descending ID so the most recently
        created workouts appear first.
        """
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Return the appropriate serializer class for the current action.

        Behaviour:
        - Use the basic workout serializer for list views.
        - Use the detail serializer for all other actions.
        """
        if self.action == "list":
            return serializers.WorkoutSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new workout owned by the authenticated user.
        Automatically assigns the current user as the workout owner.
        """
        serializer.save(user=self.request.user)


class BaseAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for simple user-owned attribute models.Access is restricted to authenticated users, and all
    queryset results are limited to objects owned by the current user.

    Intended for reusable behaviour shared by:
    - Tag viewsets
    - Exercise viewsets
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return objects belonging to the current authenticated user only.

        Results are ordered by descending name.
        """
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseAttrViewSet):
    """Manage tag API endpoints for the authenticated user."""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class ExerciseViewSet(BaseAttrViewSet):
    """Manage exercise API endpoints for the authenticated user."""

    serializer_class = serializers.ExerciseSerializer
    queryset = Exercise.objects.all()
