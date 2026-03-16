from rest_framework import serializers

from core.models import Workout


class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for workouts."""

    class Meta:
        model = Workout
        fields = ["id", "title", "duration_minutes"]
        read_only_fields = ["id"]
