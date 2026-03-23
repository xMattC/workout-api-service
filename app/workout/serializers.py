from rest_framework import serializers

from core.models import Workout, Tag, Exercise, WorkoutExercise


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    """Serialize workout exercise objects for basic CRUD operations."""

    class Meta:
        model = WorkoutExercise
        fields = ["id", "exercise", "order", "sets", "reps", "rest_seconds"]
        read_only_fields = ["id"]


class ExerciseSerializer(serializers.ModelSerializer):
    """Serialize exercise objects for basic CRUD operations."""

    class Meta:
        model = Exercise
        fields = ["id", "name"]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serialize tag objects for basic CRUD operations."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class WorkoutSerializer(serializers.ModelSerializer):
    """Serialize workout objects, including nested tag and exercise data.

    Supports:
    - Creating workouts with nested tags and workout_exercises
    - Updating workouts with replacement logic for relationships
    """

    tags = TagSerializer(many=True, required=False)
    workout_exercises = WorkoutExerciseSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "duration_minutes", "tags", "workout_exercises"]
        read_only_fields = ["id"]

    # -----------------------------------------------------------------
    # HELPER METHODS
    # -----------------------------------------------------------------

    def _get_or_create_tags(self, tags, workout):
        """Retrieve or create tag objects and assign them to the workout."""
        auth_user = self.context["request"].user

        for tag in tags:

            tag_obj, created = Tag.objects.get_or_create(user=auth_user,**tag)
            workout.tags.add(tag_obj)

    def _create_workout_exercises(self, workout_exercises, workout):
        """Create workout exercise rows for the workout."""
        for workout_exercise in workout_exercises:

            WorkoutExercise.objects.create(workout=workout,**workout_exercise)

    # -----------------------------------------------------------------
    # CREATE / UPDATE METHODS
    # -----------------------------------------------------------------

    def create(self, validated_data):
        """
        Create a new workout with optional nested tags and workout exercises.
        """
        tags = validated_data.pop("tags", [])
        workout_exercises = validated_data.pop("workout_exercises", [])

        workout = Workout.objects.create(**validated_data)

        self._get_or_create_tags(tags, workout)
        self._create_workout_exercises(workout_exercises, workout)

        return workout

    def update(self, instance, validated_data):
        """Update an existing workout, nested tags and workout exercises."""
        tags = validated_data.pop("tags", None)
        workout_exercises = validated_data.pop("workout_exercises", None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if workout_exercises is not None:
            instance.workout_exercises.clear()
            self._create_workout_exercises(workout_exercises, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class WorkoutDetailSerializer(WorkoutSerializer):
    """Extend workout serializer to include additional detail fields."""

    class Meta(WorkoutSerializer.Meta):
        fields = WorkoutSerializer.Meta.fields + ["description", "image"]


class WorkoutImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to workout."""

    class Meta:
        model = Workout
        fields = ["id", "image"]
        read_only_fields = ["id"]
        extra_kwargs = {"image": {"required": "True"}}
