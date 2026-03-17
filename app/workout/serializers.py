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

    def _get_or_create_tags(self, tags, workout):
        """Handle getting or creating tags as needed."""
        auth_user = self.context["request"].user
        for tag in tags:
            tag_object, created = Tag.objects.get_or_create(user=auth_user, **tag)
            workout.tags.add(tag_object)

    def create(self, validated_data):
        """Create a workout."""
        tags = validated_data.pop("tags", [])
        workout = Workout.objects.create(**validated_data)
        self._get_or_create_tags(tags, workout)

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
