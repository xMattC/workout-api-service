import logging

from rest_framework import serializers

from core.models import Exercise, WorkoutTag, ExerciseTag, Workout, WorkoutExercise

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# EXERCISE SERIALISERS
# ---------------------------------------------------------------------


class ExerciseTagSerializer(serializers.ModelSerializer):
    """Serialise tag objects.

    Used for:
    - Nested input when creating/updating exercises
    - Nested output when returning exercise data
    """

    class Meta:
        model = ExerciseTag
        fields = ["id", "name", "type"]
        read_only_fields = ["id"]


class ExerciseSerializer(serializers.ModelSerializer):
    """Serialise exercise objects for general API usage.

    Used for:
    - General read/write of Exercise objects
    - Nested display inside other serializers (e.g. workout detail)

    Accepts nested input for:
    - ex_tags (list of dicts)

    Key behaviour:
    - Tags are replaced, not merged
    """

    ex_tags = ExerciseTagSerializer(many=True, required=False)

    class Meta:
        model = Exercise
        fields = ["id", "name", "image_1", "image_2", "is_public", "difficulty", "ex_tags"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Validate exercise creation/update rules.

        Rules:
        - Non-staff users cannot set is_public=True
        """

        request = self.context.get("request")
        user = request.user if request else None

        # Check if user is trying to set a public exercise
        if attrs.get("is_public") is True:
            if not user or not user.is_staff:
                raise serializers.ValidationError({"is_public": "You cannot create or update a public exercise. is_public must be False!"})

        return attrs

    # -----------------------------------------------------------------
    # TAG HELPERS
    # -----------------------------------------------------------------

    def _get_or_create_tags(self, ex_tags, exercise):
        """Retrieve or create tag objects and assign them to the exercise.

        Parameters:
        - ex_tags: list of dicts, e.g. [{"name": "chest", "type": "muscle"}]
        - exercise: Exercise instance to attach ex_tags to

        Behaviour:
        - Creates tag if it does not exist for the user
        - Associates tag with exercise
        """

        auth_user = self.context["request"].user

        for tag in ex_tags:
            logger.debug("Processing exercise tag payload: %s", tag)

            tag_obj, created = ExerciseTag.objects.get_or_create(user=auth_user, **tag)

            if created:
                logger.info("Created tag '%s' (%s) for user_id=%s", tag_obj.name, tag_obj.type, auth_user.id)

            exercise.ex_tags.add(tag_obj)

        logger.debug(
            "Final ex_tags on exercise_id=%s: %s",
            exercise.id,
            list(exercise.ex_tags.values_list("name", flat=True)),
        )

    # -----------------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------------

    def create(self, validated_data):
        """Create a new exercise with optional nested ex_tags.

        Behaviour:
        - Extract nested fields from validated_data
        - Create base exercise
        - Attach ex_tags separately
        """

        ex_tags = validated_data.pop("ex_tags", [])
        exercise = Exercise.objects.create(**validated_data)

        logger.info("Exercise created id=%s", exercise.id)

        self._get_or_create_tags(ex_tags, exercise)

        return exercise

    # -----------------------------------------------------------------
    # UPDATE
    # -----------------------------------------------------------------

    def update(self, instance, validated_data):
        """Update an existing exercise.

        Behaviour:
        - ex_tags:
            - if provided → replace all ex_tags
            - if omitted → leave unchanged
        """

        ex_tags = validated_data.pop("ex_tags", None)
        logger.debug("Exercise update called with ex_tags=%s", ex_tags)

        # Replace ex_tags if explicitly provided
        if ex_tags is not None:
            instance.ex_tags.clear()
            self._get_or_create_tags(ex_tags, instance)

        # Update remaining scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        logger.info("Exercise updated id=%s", instance.id)

        return instance


class ExerciseImageSerializer(serializers.ModelSerializer):
    """Serialise exercise image uploads.

    Used by custom endpoint (e.g. POST /exercises/<id>/upload-image/).

    Behaviour:
    - Allows updating image_1 and/or image_2
    - Both fields are optional (partial updates supported)
    """

    class Meta:
        model = Exercise
        fields = ["id", "image_1", "image_2"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "image_1": {"required": False},
            "image_2": {"required": False},
        }


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


class WorkoutTagSerializer(serializers.ModelSerializer):
    """Serialise tag objects.

    Used for:
    - Nested input when creating/updating workouts
    - Nested output when returning workout data
    """

    class Meta:
        model = WorkoutTag
        fields = ["id", "name"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------
# WORKOUT SERIALISER (WRITE / BASE)
# ---------------------------------------------------------------------


class WorkoutSerializer(serializers.ModelSerializer):
    """Serialise workout objects with nested input support.

    Purpose:
    - Write operations (create/update)

    Accepts nested input for:
    - wo_tags (list of dicts)
    - workout_exercises (list of dicts)

    Key behaviour:
    - Nested relationships are replaced, not merged
    """

    # Nested writable fields (input format)
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)
    wo_tags = WorkoutTagSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "description", "duration_minutes", "wo_tags", "workout_exercises"]
        read_only_fields = ["id"]

    # -----------------------------------------------------------------
    # TAG HELPERS
    # -----------------------------------------------------------------

    def _get_or_create_tags(self, wo_tags, workout):
        """Retrieve or create tag objects and assign them to the workout.

        Parameters:
        - wo_tags: list of dicts, e.g. [{"name": "Leg Day"}]
        - workout: Workout instance to attach wo_tags to

        Behaviour:
        - Creates tag if it does not exist for the user
        - Associates tag with workout
        """

        auth_user = self.context["request"].user

        for tag in wo_tags:
            logger.debug("Processing tag payload: %s", tag)

            tag_obj, created = WorkoutTag.objects.get_or_create(user=auth_user, **tag)

            if created:
                logger.info("Created tag '%s' for user_id=%s", tag_obj.name, auth_user.id)

            workout.wo_tags.add(tag_obj)

        logger.debug(
            "Final wo_tags on workout_id=%s: %s",
            workout.id,
            list(workout.wo_tags.values_list("name", flat=True)),
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
        - Attach wo_tags and exercises separately
        """

        wo_tags = validated_data.pop("wo_tags", [])
        workout_exercises = validated_data.pop("workout_exercises", [])

        workout = Workout.objects.create(**validated_data)

        logger.info("Workout created id=%s", workout.id)

        self._get_or_create_tags(wo_tags, workout)
        self._create_workout_exercises(workout_exercises, workout)

        return workout

    # -----------------------------------------------------------------
    # UPDATE
    # -----------------------------------------------------------------

    def update(self, instance, validated_data):
        """Update an existing workout.

        Behaviour:
        - wo_tags:
            - if provided → replace all wo_tags
            - if omitted → leave unchanged

        - workout_exercises:
            - if provided → replace all exercises
            - if [] → clear all
            - if omitted → leave unchanged
        """

        wo_tags = validated_data.pop("wo_tags", None)
        workout_exercises = validated_data.pop("workout_exercises", None)

        logger.debug("Update called with wo_tags=%s", wo_tags)

        # Replace wo_tags if explicitly provided
        if wo_tags is not None:
            instance.wo_tags.clear()
            self._get_or_create_tags(wo_tags, instance)

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
