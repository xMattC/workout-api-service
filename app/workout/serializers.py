from rest_framework import serializers

from core.models import Workout, Tag


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for workouts."""

    class Meta:
        model = Workout
        fields = ["id", "title", "description", "duration_minutes"]
        read_only_fields = ["id"]


class WorkoutDetailSerializer(WorkoutSerializer):
    """Serializer for workout detail view."""

        # class Meta(WorkoutSerializer.Meta):
        #     fields = WorkoutSerializer.Meta.fields + ['description']
    pass


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']