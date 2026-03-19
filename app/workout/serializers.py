from rest_framework import serializers

from core.models import Workout, Tag, Exercise


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
    """
    Serialize workout objects, including nested tag and exercise data.

    Supports:
    - Creating workouts with nested tags and exercises
    - Updating workouts with replacement logic for relationships
    """

    tags = TagSerializer(many=True, required=False)
    exercises = ExerciseSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "duration_minutes", "tags", "exercises"]
        read_only_fields = ["id"]

    # -----------------------------------------------------------------
    # HELPER METHODS
    # -----------------------------------------------------------------

    def _get_or_create_tags(self, tags, workout):
        """
        Retrieve or create tag objects and assign them to the workout.

        Parameters:
        - tags: List of tag dictionaries from validated data.
        - workout: Workout instance to associate tags with.

        Behaviour:
        - Uses the authenticated user to scope tag ownership.
        - Reuses existing tags if they already exist.
        - Creates new tags if they do not exist.
        """
        auth_user = self.context["request"].user

        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            workout.tags.add(tag_obj)

    def _get_or_create_exercises(self, exercises, workout):
        """
        Retrieve or create exercise objects and assign them to the workout.

        Parameters:
        - exercises: List of exercise dictionaries from validated data.
        - workout: Workout instance to associate exercises with.

        Behaviour:
        - Uses the authenticated user to scope exercise ownership.
        - Reuses existing exercises if they already exist.
        - Creates new exercises if they do not exist.
        """
        auth_user = self.context["request"].user

        for exercise in exercises:
            exercise_obj, created = Exercise.objects.get_or_create(
                user=auth_user,
                **exercise,
            )
            workout.exercises.add(exercise_obj)

    # -----------------------------------------------------------------
    # CREATE / UPDATE METHODS
    # -----------------------------------------------------------------

    def create(self, validated_data):
        """
        Create a new workout with optional nested tags and exercises.

        Behaviour:
        - Extracts nested tag and exercise data if provided.
        - Creates the workout instance.
        - Associates tags and exercises via helper methods.
        """
        tags = validated_data.pop("tags", [])
        exercises = validated_data.pop("exercises", [])

        workout = Workout.objects.create(**validated_data)

        self._get_or_create_tags(tags, workout)
        self._get_or_create_exercises(exercises, workout)

        return workout

    def update(self, instance, validated_data):
        """
        Update an existing workout, including nested relationships.

        Behaviour:
        - If tags are provided:
            - Clears existing tags
            - Reassigns using provided data
        - If exercises are provided:
            - Clears existing exercises
            - Reassigns using provided data
        - Updates remaining scalar fields normally
        """
        tags = validated_data.pop("tags", None)
        exercises = validated_data.pop("exercises", None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if exercises is not None:
            instance.exercises.clear()
            self._get_or_create_exercises(exercises, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class WorkoutDetailSerializer(WorkoutSerializer):
    """Extend workout serializer to include additional detail fields."""

    class Meta(WorkoutSerializer.Meta):
        fields = WorkoutSerializer.Meta.fields + ["description"]
