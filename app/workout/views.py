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

# ---------------------------------------------------------------------
# SHARED BASE VIEWSETS / HELPERS
# ---------------------------------------------------------------------


class BaseAttrViewSet(
    mixins.CreateModelMixin,  # POST /<resource>/ -> create()
    mixins.RetrieveModelMixin,  # GET /<resource>/<id>/ -> retrieve()
    mixins.DestroyModelMixin,  # DELETE /<resource>/<id>/   -> destroy()
    mixins.UpdateModelMixin,  # PUT/PATCH -> update() / partial_update()
    mixins.ListModelMixin,  # GET /<resource>/ -> list()
    viewsets.GenericViewSet,  # wires mixin actions into URL routes
    # NOTE: This could be simplified by inheriting from `viewsets.ModelViewSet`, which already includes all of the
    # above mixins + GenericViewSet - but we want to be explicit about which actions are supported in BaseAttrViewSet.
):
    """Base viewset for simple user-owned attribute models.

    Purpose:
    - Provide shared CRUD behaviour for models owned by a user
    - Avoid duplicating logic across multiple viewsets

    Used by:
    - TagViewSet
    - ExerciseViewSet

    Key behaviour:
    - Automatically scopes all queries to the authenticated user
    - Automatically assigns the authenticated user on object creation
    - Provides standard CRUD actions via DRF mixins

    Notes:
    - This class is NOT registered with the router, so it does not create API endpoints directly
    - It is only used as a base class to share behaviour
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return objects belonging to the authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by("-name").distinct()

    def perform_create(self, serializer):
        """Create a new object owned by the authenticated user."""
        serializer.save(user=self.request.user)


# ---------------------------------------------------------------------
# API VIEWSETS
# ---------------------------------------------------------------------


@WORKOUT_VIEWSET_SCHEMA
class WorkoutViewSet(viewsets.ModelViewSet):
    """Manage workout API endpoints."""

    # ---------------------------------------------------------------------
    # ACTION BEHAVIOUR (inherited from DRF ModelViewSet)
    # ---------------------------------------------------------------------
    # - list [GET]              -> return a lightweight list representation of workouts (ListModelMixin)
    # - retrieve [GET]          -> return a detailed representation of a single workout (RetrieveModelMixin)
    # - create [POST]           -> create a workout for the authenticated user (CreateModelMixin)
    # - update [PUT]            -> fully replace editable fields on an existing workout (UpdateModelMixin)
    # - partial_update [PATCH]  -> partially update an existing workout (UpdateModelMixin)
    # - destroy [DELETE]        -> delete an existing workout (DestroyModelMixin)

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


@EXERCISE_VIEWSET_SCHEMA
class ExerciseViewSet(BaseAttrViewSet):
    """Manage exercise API endpoints for the authenticated user."""

    # ---------------------------------------------------------------------
    # ACTION BEHAVIOUR (inherited from DRF mixins via BaseAttrViewSet)
    # ---------------------------------------------------------------------
    # - list [GET]              -> return exercise objects (ListModelMixin)
    # - retrieve [GET]          -> return a single exercise (RetrieveModelMixin)
    # - create [POST]           -> create an exercise owned by the authenticated user (CreateModelMixin)
    # - update [PUT]            -> fully update an existing exercise (UpdateModelMixin)
    # - partial_update [PATCH]  -> partially update an existing exercise (UpdateModelMixin)
    # - destroy [DELETE]        -> delete an existing exercise (DestroyModelMixin)
    #
    # - upload_image [POST]     -> custom action to upload/replace exercise image (@action decorator)

    queryset = Exercise.objects.all()
    serializer_class = serializers.ExerciseSerializer

    def get_queryset(self):
        """Return exercises for the authenticated user, with optional filtering.

        Visibility rules:
        - Include the user's own exercises
        - Include public exercises created by any user
        - Exclude private exercises owned by other users
        """
        user = self.request.user
        own_exercises = self.queryset.filter(user=user)
        public_exercises = self.queryset.filter(is_public=True)

        queryset = (own_exercises | public_exercises).order_by("-name").distinct()

        # Check query param (e.g. /exercises/?assigned_only=1)
        # If set, only include exercises that are linked to at least one workout
        assigned_to_workouts_only = self.request.query_params.get("assigned_only") == "1"

        if assigned_to_workouts_only:
            queryset = queryset.filter(workout_exercises__isnull=False)

        return queryset.distinct()

    def get_serializer_class(self):
        """Return the serializer class for the current action.

        Serializer behaviour:
        - upload_image      -> ExerciseImageSerializer
        - all other actions -> ExerciseSerializer
        """
        if self.action == "upload_image":
            return serializers.ExerciseImageSerializer

        return serializers.ExerciseSerializer

    def perform_create(self, serializer):
        """Create an exercise for the authenticated user.

        Normal users always create private exercises.
        Admin users may create public exercises.
        """
        user = self.request.user

        if user.is_staff:
            serializer.save(user=user)  # Admin users can set is_public via the serializer input
        else:
            serializer.save(user=user, is_public=False)

    def perform_update(self, serializer):
        user = self.request.user

        if user.is_staff:
            serializer.save()  # Admin users can set is_public via the serializer input
        else:
            serializer.save(is_public=False)

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


@TAG_VIEWSET_SCHEMA
class TagViewSet(BaseAttrViewSet):
    """Manage tag API endpoints for the authenticated user."""

    # ---------------------------------------------------------------------
    # ACTION BEHAVIOUR (inherited from DRF mixins via BaseAttrViewSet)
    # ---------------------------------------------------------------------
    # - list [GET]              -> return tag objects (ListModelMixin)
    # - retrieve [GET]          -> return a single tag (RetrieveModelMixin)
    # - create [POST]           -> create a tag owned by the authenticated user (CreateModelMixin)
    # - update [PUT]            -> fully update an existing tag (UpdateModelMixin)
    # - partial_update [PATCH]  -> partially update an existing tag (UpdateModelMixin)
    # - destroy [DELETE]        -> delete an existing tag (DestroyModelMixin)

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
