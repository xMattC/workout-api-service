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


# ---------------------------------------------------------------------
# SWAGGER / OPENAPI DECORATORS
# ---------------------------------------------------------------------

WORKOUT_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="tags",
                type=OpenApiTypes.STR,
                description="Comma separated list of tag IDs to filter by.",
            ),
            OpenApiParameter(
                name="exercises",
                type=OpenApiTypes.STR,
                description="Comma separated list of exercise IDs to filter by.",
            ),
        ]
    )
)

TAG_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="assigned_only",
                type=OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter by tags assigned to workouts.",
            ),
        ]
    )
)

EXERCISE_VIEWSET_SCHEMA = extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="assigned_only",
                type=OpenApiTypes.INT,
                enum=[0, 1],
                description="Filter by exercises assigned to workouts.",
            ),
        ]
    )
)

EXERCISE_UPLOAD_IMAGE_SCHEMA = extend_schema(
    description="Upload or replace an image for a specific exercise.",
    request=serializers.ExerciseImageSerializer,
    responses=serializers.ExerciseImageSerializer,
)


@WORKOUT_VIEWSET_SCHEMA
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

    # Default serializer is detail; overridden for non-retrieve actions.
    serializer_class = serializers.WorkoutDetailSerializer

    def _parse_ids_param(self, qs):
        """Convert a comma-separated query parameter into a list of integers."""
        return [int(str_id) for str_id in qs.split(",") if str_id.strip().isdigit()]

    def get_queryset(self):
        """Return workouts for the authenticated user, with optional filtering."""
        tags = self.request.query_params.get("tags")
        exercises = self.request.query_params.get("exercises")

        # Always scope to authenticated user.
        queryset = self.queryset.filter(user=self.request.user)

        # Filter by tags.
        if tags:
            tag_ids = self._parse_ids_param(tags)
            if tag_ids:
                queryset = queryset.filter(tags__id__in=tag_ids)

        # Filter by exercises.
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


class BaseAttrViewSet(
    mixins.CreateModelMixin,  # provides POST /<resource>/ -> create()
    mixins.RetrieveModelMixin,  # provides GET /<resource>/<id>/ -> retrieve()
    mixins.DestroyModelMixin,  # provides DELETE /<resource>/<id>/ -> destroy()
    mixins.UpdateModelMixin,  # provides PUT/PATCH /<resource>/<id>/ -> update() / partial_update()
    mixins.ListModelMixin,  # provides GET /<resource>/ -> list()
    viewsets.GenericViewSet,  # base viewset that wires mixin actions into routes
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


@TAG_VIEWSET_SCHEMA
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
        """Return tags for the authenticated user, with optional filtering."""

        queryset = super().get_queryset()

        # Check query param (e.g. /tags/?assigned_only=1)
        # When set, only include tags that are linked to at least one workout
        assigned_to_workouts_only = self.request.query_params.get("assigned_only") == "1"

        if assigned_to_workouts_only:
            queryset = queryset.filter(workout__isnull=False)

        return queryset.distinct()


@EXERCISE_VIEWSET_SCHEMA
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
        """Return exercises for the authenticated user, with optional filtering."""

        queryset = super().get_queryset()

        # Check query param (e.g. /exercises/?assigned_only=1)
        # If set, only include exercises that are linked to at least one workout
        assigned_to_workouts_only = self.request.query_params.get("assigned_only") == "1"

        if assigned_to_workouts_only:
            queryset = queryset.filter(workout_exercises__isnull=False)

        return queryset.distinct()

    def get_serializer_class(self):
        """Return the serializer class for the current action.

        # Serializer behaviour:
        # - upload_image      -> ExerciseImageSerializer
        # - all other actions -> ExerciseSerializer
        """
        if self.action == "upload_image":
            return serializers.ExerciseImageSerializer

        return serializers.ExerciseSerializer

    @EXERCISE_UPLOAD_IMAGE_SCHEMA
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
