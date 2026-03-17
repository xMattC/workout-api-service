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

    def create(self, validated_data):
        """Create a workout."""
        tags = validated_data.pop("tags", [])
        workout = Workout.objects.create(**validated_data)
        auth_user = self.context["request"].user
        for tag in tags:
            tag_object, created = Tag.objects.get_or_create(
                user=auth_user, **tag
            )
            workout.tags.add(tag_object)

        return workout


class WorkoutDetailSerializer(WorkoutSerializer):
    """Serializer for workout detail view."""

    class Meta(WorkoutSerializer.Meta):
        fields = WorkoutSerializer.Meta.fields + ["description"]

    # pass
