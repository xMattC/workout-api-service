import logging

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Exercise, Tag, Workout
from workout import serializers


logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma separated list of tag IDs to filter by.",
            ),
            OpenApiParameter(
                "exercises",
                OpenApiTypes.STR,
                description="Comma separated list of exercise IDs to filter by.",
            ),
        ]
    )
)
class WorkoutViewSet(viewsets.ModelViewSet):
    """Manage workout API endpoints."""

    # ---------------------------------------------------------------------
    # ACTION BEHAVIOUR
    # ---------------------------------------------------------------------
    # - list [GET]              -> return a lightweight list representation of workouts
    # - retrieve [GET]          -> return a detailed representation of a single workout
    # - create [POST]           -> create a workout for the authenticated user
    # - update [PUT]            -> fully replace editable fields on an existing workout
    # - partial_update [PATCH]  -> partially update an existing workout
    # - destroy [DELETE]        -> delete an existing workout

    queryset = Workout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Default serializer is detail; overridden for non-retrieve actions
    serializer_class = serializers.WorkoutDetailSerializer

    def _parse_ids_param(self, qs):
        """Convert a comma-separated query parameter into a list of integers."""
        return [int(str_id) for str_id in qs.split(",") if str_id.strip().isdigit()]

    def get_queryset(self):
        """Return workouts for the authenticated user, with optional filtering."""
        tags = self.request.query_params.get("tags")
        exercises = self.request.query_params.get("exercises")

        # Always scope to authenticated user
        queryset = self.queryset.filter(user=self.request.user)

        # Filter by tags
        if tags:
            tag_ids = self._parse_ids_param(tags)
            if tag_ids:
                queryset = queryset.filter(tags__id__in=tag_ids)

        # Filter by exercises
        if exercises:
            exercise_ids = self._parse_ids_param(exercises)
            if exercise_ids:
                queryset = queryset.filter(workout_exercises__exercise__id__in=exercise_ids)

        return queryset.order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for the current action.

        Serializer behaviour:
        - retrieve          -> WorkoutDetailSerializer
        - all other actions -> WorkoutSerializer
        """

        if self.action == "retrieve":
            return serializers.WorkoutDetailSerializer

        return serializers.WorkoutSerializer

    def perform_create(self, serializer):
        """Create a workout owned by the authenticated user."""
        serializer.save(user=self.request.user)
        logger.info("Workout create requested by user_id=%s", self.request.user.id)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter by items assigned to workouts.",
            ),
        ]
    )
)
class BaseAttrViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for simple user-owned attribute models."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return objects belonging to the authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by("-name").distinct()

    def perform_create(self, serializer):
        """Create a new object owned by the authenticated user."""
        serializer.save(user=self.request.user)


class TagViewSet(BaseAttrViewSet):
    """Manage tag API endpoints for the authenticated user."""

    # ---------------------------------------------------------------------
    # ACTION BEHAVIOUR
    # ---------------------------------------------------------------------
    # - list [GET]              -> return tag objects
    # - retrieve [GET]          -> return a single tag
    # - create [POST]           -> create a tag owned by the authenticated user
    # - update [PUT]            -> fully update an existing tag
    # - partial_update [PATCH]  -> partially update an existing tag
    # - destroy [DELETE]        -> delete an existing tag

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

    def get_queryset(self):
        """Return tags for the authenticated user, optionally filtered by assignment."""
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        queryset = super().get_queryset()

        # Only return tags linked to workouts if requested
        if assigned_only:
            queryset = queryset.filter(workout__isnull=False)

        return queryset.distinct()


class ExerciseViewSet(BaseAttrViewSet):
    """Manage exercise API endpoints for the authenticated user."""

    # ---------------------------------------------------------------------
    # ACTION BEHAVIOUR
    # ---------------------------------------------------------------------
    # - list [GET]              -> return exercise objects
    # - retrieve [GET]          -> return a single exercise
    # - create [POST]           -> create an exercise owned by the authenticated user
    # - update [PUT]            -> fully update an existing exercise
    # - partial_update [PATCH]  -> partially update an existing exercise
    # - destroy [DELETE]        -> delete an existing exercise
    # - upload_image [POST]     -> upload or replace an exercise image

    queryset = Exercise.objects.all()
    serializer_class = serializers.ExerciseSerializer

    def get_queryset(self):
        """Return exercises for the authenticated user, optionally filtered by assignment."""
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        queryset = super().get_queryset()

        # Only return exercises used in workouts if requested
        if assigned_only:
            queryset = queryset.filter(workout_exercises__isnull=False)

        return queryset.distinct()

    def get_serializer_class(self):
        """Return the serializer class for the current action.

        Serializer behaviour:
        - upload_image    -> ExerciseImageSerializer
        - all other actions -> ExerciseSerializer
        """
        if self.action == "upload_image":
            return serializers.ExerciseImageSerializer

        return serializers.ExerciseSerializer

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload or replace an image for an exercise."""
        exercise = self.get_object()
        serializer = self.get_serializer(exercise, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        logger.warning(
            "Exercise image upload validation failed for exercise_id=%s by user_id=%s: %s",
            exercise.id,
            request.user.id,
            serializer.errors,
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
