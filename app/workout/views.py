import logging

from django.db.models import Q
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Exercise, ExerciseTag, Workout, WorkoutTag
from workout import serializers

logger = logging.getLogger(__name__)


EXERCISE_UPLOAD_IMAGE_SCHEMA = extend_schema(
    description="Upload or replace image_1 and/or image_2 for a specific exercise.",
    request=serializers.ExerciseImageSerializer,
    responses=serializers.ExerciseImageSerializer,
)


# ---------------------------------------------------------------------
# SHARED BASE VIEWSETS / HELPERS
# ---------------------------------------------------------------------
class BaseAttrViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for simple user-owned attribute models.

    Purpose:
    - Provide shared CRUD behaviour for models owned by a user
    - Avoid duplicating logic across multiple viewsets

    Used by:
    - WorkoutTagViewSet
    - ExerciseViewSet
    - ExerciseTagViewSet

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
# WorkoutViewSet - manages workouts for the authenticated user
# ---------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        description="List workouts owned by the authenticated user.",
        parameters=[
            OpenApiParameter(
                name="exercises",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of exercise IDs to filter by.",
            ),
            OpenApiParameter(
                name="wo_tags",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of workout tag IDs. Returns workouts matching any of the supplied tag IDs.", # noqa
            ),
        ],
    ),
    retrieve=extend_schema(description="Retrieve a detailed workout owned by the authenticated user."),
    create=extend_schema(description="Create a workout for the authenticated user."),
    update=extend_schema(description="Fully update a workout owned by the authenticated user."),
    partial_update=extend_schema(description="Partially update a workout owned by the authenticated user."),
    destroy=extend_schema(description="Delete a workout owned by the authenticated user."),
)
class WorkoutViewSet(viewsets.ModelViewSet):
    """Manage workout API endpoints."""

    queryset = Workout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = serializers.WorkoutDetailSerializer

    def _parse_ids_param(self, qs):
        """Convert a comma-separated query parameter into a list of integers."""
        return [int(str_id) for str_id in qs.split(",") if str_id.strip().isdigit()]

    def get_queryset(self):
        """Return workouts for the authenticated user, with optional filtering.

        Supported filters:
        - exercises: comma-separated list of exercise IDs
        - wo_tags: comma-separated list of workout tag IDs
        """
        queryset = self.queryset.filter(user=self.request.user)

        exercises = self.request.query_params.get("exercises")
        if exercises:
            exercise_ids = self._parse_ids_param(exercises)
            if exercise_ids:
                queryset = queryset.filter(workout_exercises__exercise__id__in=exercise_ids)

        wo_tags = self.request.query_params.get("wo_tags")
        if wo_tags:
            tag_ids = self._parse_ids_param(wo_tags)
            if tag_ids:
                queryset = queryset.filter(wo_tags__id__in=tag_ids)

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


# ---------------------------------------------------------------------
# WorkoutTagViewSet - manages workout tags for the authenticated user
# ---------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        description="List workout tags for the authenticated user.",
        parameters=[
            OpenApiParameter(
                name="assigned_only",
                type=OpenApiTypes.INT,
                enum=[0, 1],
                description="Set to 1 to return only workout tags assigned to at least one workout.",
            ),
        ],
    ),
    retrieve=extend_schema(description="Retrieve a workout tag owned by the authenticated user."),
    create=extend_schema(description="Create a workout tag for the authenticated user."),
    update=extend_schema(description="Fully update a workout tag owned by the authenticated user."),
    partial_update=extend_schema(description="Partially update a workout tag owned by the authenticated user."),
    destroy=extend_schema(description="Delete a workout tag owned by the authenticated user."),
)
class WorkoutTagViewSet(BaseAttrViewSet):
    """Manage workout tag API endpoints for the authenticated user."""

    serializer_class = serializers.WorkoutTagSerializer
    queryset = WorkoutTag.objects.all()

    def get_queryset(self):
        """Return workout tags for the authenticated user, with optional filtering.

        Supported filters:
        - assigned_only=1 -> only tags linked to at least one workout
        """
        queryset = super().get_queryset()

        assigned_only = self.request.query_params.get("assigned_only") == "1"
        if assigned_only:
            queryset = queryset.filter(workouts__isnull=False)

        return queryset.distinct()


# ---------------------------------------------------------------------
# ExerciseViewSet - manages exercises for the authenticated user, including public exercises
# ---------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        description="List exercises visible to the authenticated user.",
        parameters=[
            OpenApiParameter(
                name="assigned_only",
                type=OpenApiTypes.INT,
                enum=[0, 1],
                description="Set to 1 to return only exercises assigned to at least one workout.",
            ),
            OpenApiParameter(
                name="ex_tags",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of exercise tag IDs to filter by.",
            ),
        ],
    ),
    retrieve=extend_schema(description="Retrieve an exercise if it is public or owned by the authenticated user."),
    create=extend_schema(description="Create an exercise for the authenticated user."),
    update=extend_schema(description="Fully update an exercise owned by the authenticated user."),
    partial_update=extend_schema(description="Partially update an exercise owned by the authenticated user."),
    destroy=extend_schema(description="Delete an exercise owned by the authenticated user."),
)
class ExerciseViewSet(BaseAttrViewSet):
    """Manage exercise API endpoints for the authenticated user."""

    queryset = Exercise.objects.all()
    serializer_class = serializers.ExerciseSerializer

    def _parse_ids_param(self, qs):
        """Convert a comma-separated query parameter into a list of integers."""
        return [int(str_id) for str_id in qs.split(",") if str_id.strip().isdigit()]

    def get_queryset(self):
        """Return exercises visible to the authenticated user, with optional filtering."""
        queryset = self.queryset.filter(Q(user=self.request.user) | Q(is_public=True))

        assigned_only = self.request.query_params.get("assigned_only") == "1"
        if assigned_only:
            queryset = queryset.filter(workout_exercises__isnull=False)

        ex_tags = self.request.query_params.get("ex_tags")
        if ex_tags:
            tag_ids = self._parse_ids_param(ex_tags)
            if tag_ids:
                queryset = queryset.filter(ex_tags__id__in=tag_ids)

        return queryset.order_by("-name").distinct()

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
            serializer.save(user=user)
        else:
            serializer.save(user=user, is_public=False)

    def perform_update(self, serializer):
        """Update an exercise for the authenticated user.

        Normal users may not make exercises public.
        Admin users may update public visibility.
        """
        user = self.request.user

        if user.is_staff:
            serializer.save()
        else:
            serializer.save(is_public=False)

    # ---------------------------------------------------------------------
    # Custom action for uploading/replacing exercise images
    # ---------------------------------------------------------------------
    @action(methods=["POST"], detail=True, url_path="upload-image")
    @extend_schema(
        description="Upload or replace image_1 and/or image_2 for a specific exercise.",
        request=serializers.ExerciseImageSerializer,
        responses=serializers.ExerciseImageSerializer,
    )
    def upload_image(self, request, pk=None):
        """Upload or replace an image for an exercise."""
        exercise = self.get_object()
        serializer = self.get_serializer(exercise, data=request.data, partial=True)

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


# ---------------------------------------------------------------------
# ExerciseTagViewSet - manages exercise tags for the authenticated user, including system-defined tags
# ---------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        description="List system exercise tags and the authenticated user's custom exercise tags.",
        parameters=[
            OpenApiParameter(
                name="assigned_only",
                type=OpenApiTypes.INT,
                enum=[0, 1],
                description="Set to 1 to return only exercise tags assigned to at least one exercise.",
            ),
        ],
    ),
    retrieve=extend_schema(
        description="Retrieve an exercise tag if it is system-defined or owned by the authenticated user."
    ),
    create=extend_schema(description="Create a custom exercise tag for the authenticated user."),
    update=extend_schema(description="Fully update an exercise tag only if it is user-owned and custom."),
    partial_update=extend_schema(description="Partially update an exercise tag only if it is user-owned and custom."),
    destroy=extend_schema(description="Delete an exercise tag only if it is user-owned and custom."),
)
class ExerciseTagViewSet(BaseAttrViewSet):
    """Manage exercise tag API endpoints."""

    serializer_class = serializers.ExerciseTagSerializer
    queryset = ExerciseTag.objects.all().order_by("name", "id")

    def get_queryset(self):
        """Return system exercise tags and the authenticated user's custom exercise tags.

        Supported filters:
        - assigned_only=1 -> only tags linked to at least one exercise
        """
        queryset = self.queryset.filter(Q(is_system=True) | Q(user=self.request.user))

        assigned_only = self.request.query_params.get("assigned_only") == "1"
        if assigned_only:
            queryset = queryset.filter(exercises__isnull=False)

        return queryset.distinct()

    def perform_create(self, serializer):
        """Create a custom exercise tag for the authenticated user."""
        serializer.save(user=self.request.user, is_system=False)

    def perform_update(self, serializer):
        """Update a user-owned custom exercise tag."""
        if serializer.instance.is_system or serializer.instance.user != self.request.user:
            raise PermissionDenied("You cannot modify system exercise tags.")
        serializer.save()

    def perform_destroy(self, instance):
        """Delete a user-owned custom exercise tag."""
        if instance.is_system or instance.user != self.request.user:
            raise PermissionDenied("You cannot delete system exercise tags.")
        instance.delete()
