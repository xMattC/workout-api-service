import logging

from rest_framework import serializers

from core.models import Exercise, Tag, Workout, WorkoutExercise


class ExerciseSerializer(serializers.ModelSerializer):
    """Serialise exercise objects for general API usage."""

    class Meta:
        model = Exercise
        fields = ["id", "name", "image"]
        read_only_fields = ["id"]


class ExerciseImageSerializer(serializers.ModelSerializer):
    """Serialise exercise image uploads only."""

    class Meta:
        model = Exercise
        fields = ["id", "image"]
        read_only_fields = ["id"]
        extra_kwargs = {"image": {"required": True}}


logger = logging.getLogger(__name__)


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    """Serialise workout exercise rows for create and update operations."""

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise", "order", "sets", "reps", "rest_seconds"]
        read_only_fields = ["id"]


class WorkoutExerciseDetailSerializer(serializers.ModelSerializer):
    """Serialise workout exercise rows with nested exercise detail for reads."""

    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise", "order", "sets", "reps", "rest_seconds"]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serialise tag objects for general API usage."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class WorkoutSerializer(serializers.ModelSerializer):
    """Serialise workout objects with nested tag and workout exercise input.

    Supports:
    - Creating workouts with nested tags and workout_exercises.
    - Updating workouts with replacement logic for nested relationships.
    """

    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "duration_minutes", "tags", "workout_exercises"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, workout):
        """Retrieve or create tag objects and assign them to the workout."""
        auth_user = self.context["request"].user

        for tag in tags:

            logger.debug("Processing tag payload: %s", tag)

            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)

            if created:
                logger.info(
                    "Created tag '%s' for user_id=%s",
                    tag_obj.name,
                    auth_user.id,
                )

            workout.tags.add(tag_obj)

        logger.debug(
            "Final tags on workout_id=%s: %s",
            workout.id,
            list(workout.tags.values_list("name", flat=True)),
        )

    def _create_workout_exercises(self, workout_exercises, workout):
        """Create workout exercise rows for the workout."""
        for workout_exercise in workout_exercises:
            WorkoutExercise.objects.create(workout=workout, **workout_exercise)

    def create(self, validated_data):
        """Create a new workout with optional nested tags and workout exercises."""
        tags = validated_data.pop("tags", [])
        workout_exercises = validated_data.pop("workout_exercises", [])

        workout = Workout.objects.create(**validated_data)

        logger.info("Workout created id=%s", workout.id)

        self._get_or_create_tags(tags, workout)
        self._create_workout_exercises(workout_exercises, workout)

        return workout

    def update(self, instance, validated_data):
        """Update an existing workout, including nested tags and workout exercises."""
        tags = validated_data.pop("tags", None)
        workout_exercises = validated_data.pop("workout_exercises", None)
        logger.debug("Update called with tags=%s", tags)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if workout_exercises is not None:
            instance.workout_exercises.all().delete()
            self._create_workout_exercises(workout_exercises, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        logger.info("Workout updated id=%s", instance.id)

        return instance


class WorkoutDetailSerializer(serializers.ModelSerializer):
    """Serialise workout objects with expanded detail for retrieve operations."""

    # tags = TagSerializer(many=True, read_only=False)
    workout_exercises = WorkoutExerciseDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = ["id", "title", "description", "duration_minutes", "tags", "workout_exercises"]
        read_only_fields = ["id"]
