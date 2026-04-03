from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core import models


# ---------------------------------------------------------------------
# READ-ONLY ADMIN MIXIN
# ---------------------------------------------------------------------
class ReadOnlyAdminMixin:
    def _is_read_only(self, request):
        return request.user.is_staff and not request.user.is_superuser

    def has_add_permission(self, request):
        if self._is_read_only(request):
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if self._is_read_only(request):
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if self._is_read_only(request):
            return request.method in ["GET", "HEAD", "OPTIONS"]
        return super().has_change_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if self._is_read_only(request):
            model_field_names = [field.name for field in self.model._meta.fields]
            existing_readonly_fields = list(super().get_readonly_fields(request, obj))
            return list(dict.fromkeys(model_field_names + existing_readonly_fields))

        return super().get_readonly_fields(request, obj)


class UserAdmin(ReadOnlyAdminMixin, BaseUserAdmin):

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    ordering = ["id"]
    list_display = ["email", "name", "is_staff", "is_active"]
    search_fields = ["email", "name"]
    list_filter = ["is_staff", "is_superuser", "is_active"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    readonly_fields = ["last_login"]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )


# ---------------------------------------------------------------------
# WORKOUT ADMIN FORM
# ---------------------------------------------------------------------
class WorkoutAdminForm(forms.ModelForm):
    class Meta:
        model = models.Workout
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "cols": 80,
                    "style": "max-width: 900px;",
                }
            ),
        }


# ---------------------------------------------------------------------
# WORKOUT EXERCISE INLINE FORM
# ---------------------------------------------------------------------
class WorkoutExerciseInlineForm(forms.ModelForm):
    class Meta:
        model = models.WorkoutExercise
        fields = "__all__"
        widgets = {
            "user_notes": forms.Textarea(
                attrs={
                    "rows": 2,
                    "cols": 32,
                    "style": "min-width: 260px; max-width: 420px;",
                }
            ),
        }


# ---------------------------------------------------------------------
# WORKOUT EXERCISE INLINE
# ---------------------------------------------------------------------
class WorkoutExerciseInline(admin.TabularInline):
    model = models.WorkoutExercise
    form = WorkoutExerciseInlineForm
    extra = 0
    autocomplete_fields = ["exercise"]
    ordering = ["order"]
    show_change_link = True
    # classes = ("collapse",)
    verbose_name = "Workout exercise"
    verbose_name_plural = "Workout exercises"

    readonly_fields = ["exercise_images", "exercise_badges"]

    fields = [
        "exercise",
        "exercise_images",
        "exercise_badges",
        "order",
        "sets",
        "reps",
        "rest_seconds",
        "user_notes",
    ]

    # ---------------------------------------------------------------------
    # Render exercise images side by side with a small gap.
    #
    # Parameters:
    # - obj : WorkoutExercise instance.
    #
    # Returns:
    # - HTML containing up to two side-by-side image previews.
    # ---------------------------------------------------------------------
    def exercise_images(self, obj):
        if not obj or not obj.pk or not obj.exercise:
            return "No images"

        images = []

        if obj.exercise.image_1:
            images.append(
                '<img src="{}" style="height:72px; width:auto; border-radius:8px; object-fit:cover; border:1px solid #ddd; margin-right:8px;" />'.format(  # noqa: E501
                    obj.exercise.image_1.url
                )
            )

        if obj.exercise.image_2:
            images.append(
                '<img src="{}" style="height:72px; width:auto; border-radius:8px; object-fit:cover; border:1px solid #ddd;" />'.format(  # noqa: E501
                    obj.exercise.image_2.url
                )
            )

        if not images:
            return "No images"

        return format_html(
            '<div style="display:flex; align-items:center; gap:8px; min-width:160px;">{}</div>',
            format_html("".join(images)),
        )

    exercise_images.short_description = "Images"

    # ---------------------------------------------------------------------
    # Render compact coloured badges for exercise difficulty and visibility.
    #
    # Parameters:
    # - obj : WorkoutExercise instance.
    #
    # Returns:
    # - HTML badges summarising linked exercise metadata.
    # ---------------------------------------------------------------------
    def exercise_badges(self, obj):
        if not obj or not obj.pk or not obj.exercise:
            return "-"

        difficulty_colour_map = {
            models.Exercise.DIFFICULTY_BEGINNER: "#2e7d32",
            models.Exercise.DIFFICULTY_INTERMEDIATE: "#ef6c00",
            models.Exercise.DIFFICULTY_ADVANCED: "#c62828",
        }

        difficulty_badge = format_html(
            '<span style="display:inline-block; color:white; background:{}; padding:3px 8px; border-radius:999px; font-size:11px; font-weight:600; margin-right:6px;">{}</span>',  # noqa: E501
            difficulty_colour_map.get(obj.exercise.difficulty, "#616161"),
            obj.exercise.get_difficulty_display(),
        )

        visibility_badge = format_html(
            '<span style="display:inline-block; color:white; background:{}; padding:3px 8px; border-radius:999px; font-size:11px; font-weight:600;">{}</span>',  # noqa: E501
            "#1565c0" if obj.exercise.is_public else "#6d4c41",
            "Public" if obj.exercise.is_public else "Private",
        )

        return format_html("{}{}", difficulty_badge, visibility_badge)

    exercise_badges.short_description = "Status"


# ---------------------------------------------------------------------
# WORKOUT ADMIN
# ---------------------------------------------------------------------
class WorkoutAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    form = WorkoutAdminForm
    inlines = [WorkoutExerciseInline]

    list_display = [
        "id",
        "title",
        "user",
        "duration_minutes",
        "exercise_count",
        "tag_list",
    ]
    list_display_links = ["title"]
    list_filter = ["user", "wo_tags"]
    search_fields = ["title", "user__email", "user__name"]
    ordering = ["user", "title"]
    list_select_related = ["user"]

    autocomplete_fields = ["wo_tags"]
    filter_horizontal = ["wo_tags"]

    save_on_top = True

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("user", "title", "description"),
            },
        ),
        (
            "Structure",
            {
                "fields": ("duration_minutes", "wo_tags"),
                # "classes": ("collapse",),
                "description": "Workout organisation and tag assignment.",
            },
        ),
    )

    # ---------------------------------------------------------------------
    # Return the number of exercises attached to a workout (with badge).
    #
    # Parameters:
    # - obj : Workout instance.
    #
    # Returns:
    # - HTML badge showing count of related workout exercises.
    # ---------------------------------------------------------------------
    def exercise_count(self, obj):
        count = obj.workout_exercises.count()
        colour = "#2e7d32" if count > 0 else "#c62828"

        return format_html(
            '<span style="color: white; background: {}; padding: 4px 8px; border-radius: 999px; font-weight: 600;">{}</span>',  # noqa: E501
            colour,
            count,
        )

    exercise_count.short_description = "Exercises"

    # ---------------------------------------------------------------------
    # Render comma-separated tag list.
    #
    # Parameters:
    # - obj : Workout instance.
    #
    # Returns:
    # - String of related workout tag names.
    # ---------------------------------------------------------------------
    def tag_list(self, obj):
        return ", ".join(tag.name for tag in obj.wo_tags.all())

    tag_list.short_description = "Tags"

    # ---------------------------------------------------------------------
    # Optimise queryset.
    #
    # Parameters:
    # - request : Current admin request.
    #
    # Returns:
    # - Queryset with related user selected and tags prefetched.
    # ---------------------------------------------------------------------
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").prefetch_related("wo_tags")


# ---------------------------------------------------------------------
# WORKOUT TAG ADMIN
# ---------------------------------------------------------------------
class WorkoutTagAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["id", "name", "user", "workout_count"]
    list_display_links = ["name"]
    list_filter = ["user"]
    search_fields = ["name", "user__email", "user__name"]
    ordering = ["name"]
    list_select_related = ["user"]
    save_on_top = True

    # ---------------------------------------------------------------------
    # Count workouts using this tag.
    #
    # Parameters:
    # - obj : WorkoutTag instance.
    #
    # Returns:
    # - Integer count of related workouts.
    # ---------------------------------------------------------------------
    def workout_count(self, obj):
        return obj.workouts.count()

    workout_count.short_description = "Workouts"


# ---------------------------------------------------------------------
# EXERCISE ADMIN
# ---------------------------------------------------------------------
class ExerciseAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "user",
        "difficulty_badge",
        "visibility_badge",
        # "image_status",
        "image_1_preview",
        "image_2_preview",
        "tag_count",
    ]
    list_display_links = ["name"]
    list_filter = ["difficulty", "is_public", "user", "ex_tags__type"]
    search_fields = ["name", "user__email", "user__name", "ex_tags__name"]
    ordering = ["user", "name"]
    list_select_related = ["user"]

    autocomplete_fields = ["ex_tags"]

    readonly_fields = [
        "image_1_preview",
        "image_2_preview",
        "tag_list",
        "image_status",
    ]

    save_on_top = True
    actions = ["make_public", "make_private"]

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("name", "user", "difficulty", "is_public"),
            },
        ),
        (
            "Images",
            {
                "fields": (
                    "image_status",
                    "image_1",
                    "image_1_preview",
                    "image_2",
                    "image_2_preview",
                )
            },
        ),
        (
            "Classification",
            {
                "fields": ("ex_tags", "tag_list"),
                # "classes": ("collapse",),
            },
        ),
    )

    # ---------------------------------------------------------------------
    # Render difficulty badge.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - HTML badge showing exercise difficulty.
    # ---------------------------------------------------------------------
    def difficulty_badge(self, obj):
        colour_map = {
            models.Exercise.DIFFICULTY_BEGINNER: "#2e7d32",
            models.Exercise.DIFFICULTY_INTERMEDIATE: "#ef6c00",
            models.Exercise.DIFFICULTY_ADVANCED: "#c62828",
        }

        return format_html(
            '<span style="color: white; background: {}; padding: 4px 8px; border-radius: 999px; font-weight: 600;">{}</span>',  # noqa: E501
            colour_map.get(obj.difficulty, "#616161"),
            obj.get_difficulty_display(),
        )

    difficulty_badge.short_description = "Difficulty"

    # ---------------------------------------------------------------------
    # Render visibility badge.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - HTML badge showing public/private state.
    # ---------------------------------------------------------------------
    def visibility_badge(self, obj):
        if obj.is_public:
            return format_html(
                '<span style="color: white; background: #1565c0; padding: 4px 8px; border-radius: 999px; font-weight: 600;">Public</span>'  # noqa: E501
            )

        return format_html(
            '<span style="color: white; background: #6d4c41; padding: 4px 8px; border-radius: 999px; font-weight: 600;">Private</span>'  # noqa: E501
        )

    visibility_badge.short_description = "Visibility"

    # ---------------------------------------------------------------------
    # Render image presence badge.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - HTML badge summarising image availability.
    # ---------------------------------------------------------------------
    def image_status(self, obj):
        has_image_1 = bool(obj.image_1)
        has_image_2 = bool(obj.image_2)

        if has_image_1 and has_image_2:
            return format_html(
                '<span style="background:#2e7d32;color:white;padding:4px 8px;border-radius:999px;font-weight:600;">2 Images</span>'  # noqa: E501
            )

        if has_image_1 or has_image_2:
            return format_html(
                '<span style="background:#ef6c00;color:white;padding:4px 8px;border-radius:999px;font-weight:600;">1 Image</span>'  # noqa: E501
            )

        return format_html(
            '<span style="background:#c62828;color:white;padding:4px 8px;border-radius:999px;font-weight:600;">No Images</span>'  # noqa: E501
        )

    image_status.short_description = "Images"

    # ---------------------------------------------------------------------
    # Render preview for image_1.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - HTML image preview or fallback text.
    # ---------------------------------------------------------------------
    def image_1_preview(self, obj):
        if obj.image_1:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;" />',
                obj.image_1.url,
            )
        return "No image"

    image_1_preview.short_description = "Image 1 Preview"

    # ---------------------------------------------------------------------
    # Render preview for image_2.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - HTML image preview or fallback text.
    # ---------------------------------------------------------------------
    def image_2_preview(self, obj):
        if obj.image_2:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;" />',
                obj.image_2.url,
            )
        return "No image"

    image_2_preview.short_description = "Image 2 Preview"

    # ---------------------------------------------------------------------
    # Return count of related tags.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - Integer count of related tags.
    # ---------------------------------------------------------------------
    def tag_count(self, obj):
        return obj.ex_tags.count()

    tag_count.short_description = "Tags"

    # ---------------------------------------------------------------------
    # Render comma-separated list of tags.
    #
    # Parameters:
    # - obj : Exercise instance.
    #
    # Returns:
    # - String of related tags.
    # ---------------------------------------------------------------------
    def tag_list(self, obj):
        return ", ".join(str(tag) for tag in obj.ex_tags.all())

    tag_list.short_description = "Tags"

    # ---------------------------------------------------------------------
    # Bulk action to mark exercises public.
    #
    # Parameters:
    # - request  : Current admin request.
    # - queryset : Selected Exercise queryset.
    #
    # Returns:
    # - None.
    # ---------------------------------------------------------------------
    @admin.action(description="Mark selected exercises as public")
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} exercise(s) marked as public.")

    # ---------------------------------------------------------------------
    # Bulk action to mark exercises private.
    #
    # Parameters:
    # - request  : Current admin request.
    # - queryset : Selected Exercise queryset.
    #
    # Returns:
    # - None.
    # ---------------------------------------------------------------------
    @admin.action(description="Mark selected exercises as private")
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f"{updated} exercise(s) marked as private.")

    # ---------------------------------------------------------------------
    # Optimise queryset.
    #
    # Parameters:
    # - request : Current admin request.
    #
    # Returns:
    # - Queryset with related user selected and tags prefetched.
    # ---------------------------------------------------------------------
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").prefetch_related("ex_tags")


# ---------------------------------------------------------------------
# EXERCISE TAG ADMIN
# ---------------------------------------------------------------------
class ExerciseTagAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["id", "name", "type_badge", "owner_badge", "exercise_count"]
    list_display_links = ["name"]
    list_filter = ["type", "is_system", "user"]
    search_fields = ["name", "user__email", "user__name"]
    ordering = ["type", "user", "name"]
    list_select_related = ["user"]
    save_on_top = True

    # ---------------------------------------------------------------------
    # Render tag type badge.
    #
    # Parameters:
    # - obj : ExerciseTag instance.
    #
    # Returns:
    # - HTML badge for tag type.
    # ---------------------------------------------------------------------
    def type_badge(self, obj):
        colour_map = {
            models.ExerciseTag.TYPE_EQUIPMENT: "#3949ab",
            models.ExerciseTag.TYPE_CATEGORY: "#00897b",
            models.ExerciseTag.PRIMARY_MUSCLE: "#6a1b9a",
            models.ExerciseTag.SECONDARY_MUSCLE: "#ad1457",
        }

        return format_html(
            '<span style="color:white;background:{};padding:4px 8px;border-radius:999px;font-weight:600;">{}</span>',  # noqa: E501
            colour_map.get(obj.type, "#616161"),
            obj.get_type_display(),
        )

    type_badge.short_description = "Type"

    # ---------------------------------------------------------------------
    # Render ownership badge.
    #
    # Parameters:
    # - obj : ExerciseTag instance.
    #
    # Returns:
    # - HTML badge for system/user ownership state.
    # ---------------------------------------------------------------------
    def owner_badge(self, obj):
        if obj.is_system:
            return format_html(
                '<span style="background:#1565c0;color:white;padding:4px 8px;border-radius:999px;font-weight:600;">System</span>'  # noqa: E501
            )

        if obj.user:
            return format_html(
                '<span style="background:#6d4c41;color:white;padding:4px 8px;border-radius:999px;font-weight:600;">User</span>'  # noqa: E501
            )

        return format_html(
            '<span style="background:#757575;color:white;padding:4px 8px;border-radius:999px;font-weight:600;">Unassigned</span>'  # noqa: E501
        )

    owner_badge.short_description = "Owner"

    # ---------------------------------------------------------------------
    # Return number of linked exercises.
    #
    # Parameters:
    # - obj : ExerciseTag instance.
    #
    # Returns:
    # - Integer count of related exercises.
    # ---------------------------------------------------------------------
    def exercise_count(self, obj):
        return obj.exercises.count()

    exercise_count.short_description = "Exercises"

    # ---------------------------------------------------------------------
    # Optimise queryset.
    #
    # Parameters:
    # - request : Current admin request.
    #
    # Returns:
    # - Queryset with related user selected and exercises prefetched.
    # ---------------------------------------------------------------------
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").prefetch_related("exercises")


# ---------------------------------------------------------------------
# WORKOUT EXERCISE ADMIN
# ---------------------------------------------------------------------
class WorkoutExerciseAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "workout",
        "exercise",
        "order",
        "sets",
        "reps",
        "rest_seconds",
    ]
    list_display_links = ["workout"]
    list_filter = ["workout", "exercise"]
    search_fields = [
        "workout__title",
        "exercise__name",
        "workout__user__email",
        "workout__user__name",
    ]

    ordering = ["workout", "order"]
    autocomplete_fields = ["workout", "exercise"]
    save_on_top = True

    # ---------------------------------------------------------------------
    # Optimise queryset.
    #
    # Parameters:
    # - request : Current admin request.
    #
    # Returns:
    # - Queryset with related workout and exercise selected.
    # ---------------------------------------------------------------------
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("workout", "exercise")


# ---------------------------------------------------------------------
# REGISTER MODELS
# ---------------------------------------------------------------------
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Workout, WorkoutAdmin)
admin.site.register(models.WorkoutTag, WorkoutTagAdmin)
admin.site.register(models.Exercise, ExerciseAdmin)
admin.site.register(models.ExerciseTag, ExerciseTagAdmin)
admin.site.register(models.WorkoutExercise, WorkoutExerciseAdmin)
