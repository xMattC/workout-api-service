from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Workout, Tag, Exercise
from workout import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'exercises',
                OpenApiTypes.STR,
                description='Comma separated list of exercise IDs to filter',
            ),
        ]
    )
)
class WorkoutViewSet(viewsets.ModelViewSet):
    """Manage workout API endpoints. Access is restricted to authenticated users, and all queryset results are limited
    to objects owned by the current user.
    """

    serializer_class = serializers.WorkoutDetailSerializer
    queryset = Workout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a comma-separated string of IDs to a list of integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Return workouts for the authenticated user only."""
        tags = self.request.query_params.get("tags")
        exercises = self.request.query_params.get("exercises")
        queryset = self.queryset

        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)

        if exercises:
            exercise_ids = self._params_to_ints(exercises)
            queryset = queryset.filter(exercises__id__in=exercise_ids)

        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the appropriate serializer class for the current action.

        Behaviour:
        - Use the basic workout serializer for list views.
        - Use the detail serializer for all other actions.
        """
        if self.action == "list":
            return serializers.WorkoutSerializer

        elif self.action == "upload_image":
            return serializers.WorkoutImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new workout owned by the authenticated user.
        Automatically assigns the current user as the workout owner.
        """
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to workout."""
        workout = self.get_object()
        serializer = self.get_serializer(workout, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
