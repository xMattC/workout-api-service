from rest_framework import serializers

from core.models import Workout, Tag, Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for exercises."""

    class Meta:
        model = Exercise
        fields = ["id", "name"]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for workouts."""

    tags = TagSerializer(many=True, required=False)
    exercises = ExerciseSerializer(many=True, required=False)

    class Meta:
        model = Workout
        fields = ["id", "title", "duration_minutes", "tags", "exercises"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, workout):
        """Handle getting or creating tags as needed."""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_object, created = Tag.objects.get_or_create(user=auth_user, **tag)
            workout.tags.add(tag_object)

    def _get_or_create_exercises(self, exercises, recipe):
        """Handle getting or creating exercises as needed."""
        auth_user = self.context["request"].user
        for exercise in exercises:
            exercise_obj, created = Exercise.objects.get_or_create(
                user=auth_user,
                **exercise,
            )
            recipe.exercises.add(exercise_obj)

    def create(self, validated_data):
        """Create a workout."""
        tags = validated_data.pop("tags", [])
        exercises = validated_data.pop("exercises", [])
        workout = Workout.objects.create(**validated_data)
        self._get_or_create_tags(tags, workout)
        self._get_or_create_exercises(exercises, workout)

        return workout

    def update(self, instance, validated_data):
        """Update recipe."""
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class WorkoutDetailSerializer(WorkoutSerializer):
    """Serializer for workout detail view."""

    class Meta(WorkoutSerializer.Meta):
        fields = WorkoutSerializer.Meta.fields + ["description"]
