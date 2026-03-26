import logging

from rest_framework import serializers

from core.models import Exercise, Tag, Workout, WorkoutExercise

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# EXERCISE SERIALISERS
# ---------------------------------------------------------------------


class ExerciseSerializer(serializers.ModelSerializer):
    """Serialise exercise objects for general API usage.

    Used for:
    - General read/write of Exercise objects
    - Nested display inside other serializers (e.g. workout detail)
    """

    class Meta:
        model = Exercise
        fields = ["id", "name", "image"]
        read_only_fields = ["id"]


class ExerciseImageSerializer(serializers.ModelSerializer):
    """Serialise exercise image uploads only.

    Used by custom endpoint (e.g. POST /exercises/<id>/upload-image/).
    Restricts input to image field only.
    """

    class Meta:
        model = Exercise
        fields = ["id", "image"]
        read_only_fields = ["id"]
        extra_kwargs = {"image": {"required": True}}


# ---------------------------------------------------------------------
# WORKOUT EXERCISE SERIALISERS
# ---------------------------------------------------------------------


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    """Serialise workout exercise rows for create and update operations.

    Input format (write - POST / PUT / PATCH):
    - Expects exercise as ID
    - Used when creating/updating workouts
    """

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise", "order", "sets", "reps", "rest_seconds"]
        read_only_fields = ["id"]


class WorkoutExerciseDetailSerializer(serializers.ModelSerializer):
    """Serialise workout exercise rows with nested exercise detail for reads.

    Output format (read - GET):
    - Expands exercise into full object instead of ID
    - Used for retrieve endpoints
    """

    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise", "order", "sets", "reps", "rest_seconds"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------
# TAG SERIALISER
# ---------------------------------------------------------------------


class TagSerializer(serializers.ModelSerializer):
    """Serialise tag objects.

    Used for:
    - Nested input (create/update)
    - Nested output (read)
    """

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------
# WORKOUT SERIALISER (WRITE / BASE)
# ---------------------------------------------------------------------


class WorkoutSerializer(serializers.ModelSerializer):
    """Serialise workout objects with nested input support.

    Purpose Write operations (create/update):
    - Accepts nested input for:
        - tags (list of dicts)
        - workout_exercises (list of dicts)

    Key behaviour:
    - Nested relationships are replaced, not merged
    """

    # Nested writable fields (input format)
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "description", "duration_minutes", "tags", "workout_exercises"]
        read_only_fields = ["id"]

    # -----------------------------------------------------------------
    # TAG HELPERS
    # -----------------------------------------------------------------

    def _get_or_create_tags(self, tags, workout):
        """Retrieve or create tag objects and assign them to the workout.

        Parameters:
        - tags: list of dicts, e.g. [{"name": "Leg Day"}]
        - workout: Workout instance to attach tags to

        Behaviour:
        - Creates tag if it does not exist for the user
        - Associates tag with workout
        """

        auth_user = self.context["request"].user

        for tag in tags:
            logger.debug("Processing tag payload: %s", tag)

            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)

            if created:
                logger.info("Created tag '%s' for user_id=%s", tag_obj.name, auth_user.id)

            workout.tags.add(tag_obj)

        logger.debug(
            "Final tags on workout_id=%s: %s",
            workout.id,
            list(workout.tags.values_list("name", flat=True)),
        )

    # -----------------------------------------------------------------
    # WORKOUT EXERCISE HELPERS
    # -----------------------------------------------------------------

    def _create_workout_exercises(self, workout_exercises, workout):
        """Create workout exercise rows for the workout.

        Parameters:
        - workout_exercises: list of dicts
        - workout: Workout instance
        """

        for workout_exercise in workout_exercises:
            WorkoutExercise.objects.create(workout=workout, **workout_exercise)

    # -----------------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------------

    def create(self, validated_data):
        """Create a new workout with optional nested relationships.

        Behaviour:
        - Extract nested fields from validated_data
        - Create base workout
        - Attach tags and exercises separately
        """

        tags = validated_data.pop("tags", [])
        workout_exercises = validated_data.pop("workout_exercises", [])

        workout = Workout.objects.create(**validated_data)

        logger.info("Workout created id=%s", workout.id)

        self._get_or_create_tags(tags, workout)
        self._create_workout_exercises(workout_exercises, workout)

        return workout

    # -----------------------------------------------------------------
    # UPDATE
    # -----------------------------------------------------------------

    def update(self, instance, validated_data):
        """Update an existing workout.

        Behaviour:
        - tags:
            - if provided → replace all tags
            - if omitted → leave unchanged

        - workout_exercises:
            - if provided → replace all exercises
            - if [] → clear all
            - if omitted → leave unchanged
        """

        tags = validated_data.pop("tags", None)
        workout_exercises = validated_data.pop("workout_exercises", None)

        logger.debug("Update called with tags=%s", tags)

        # Replace tags if explicitly provided
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        # Replace exercises if explicitly provided
        if workout_exercises is not None:
            instance.workout_exercises.all().delete()
            self._create_workout_exercises(workout_exercises, instance)

        # Update remaining scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        logger.info("Workout updated id=%s", instance.id)

        return instance


# ---------------------------------------------------------------------
# WORKOUT DETAIL SERIALISER (READ ONLY / EXPANDED)
# ---------------------------------------------------------------------


class WorkoutDetailSerializer(WorkoutSerializer):
    """Serialise workout objects with expanded nested output.

    Purpose:
    - Used for retrieve (GET /workouts/<id>/)
    - Provides richer nested data for frontend consumption

    Key differences vs WorkoutSerializer:
    - workout_exercises:
        - expanded with full exercise details
        - read_only → not used for writes
    """

    workout_exercises = WorkoutExerciseDetailSerializer(many=True, read_only=True)
