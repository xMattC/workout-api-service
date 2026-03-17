from rest_framework import serializers

from core.models import Workout, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for workouts."""

    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = Workout
        fields = ["id", "title", "duration_minutes", "tags"]
        read_only_fields = ["id"]


class WorkoutDetailSerializer(WorkoutSerializer):
    """Serializer for workout detail view."""

    class Meta(WorkoutSerializer.Meta):
        fields = WorkoutSerializer.Meta.fields + ["description"]

    # pass
