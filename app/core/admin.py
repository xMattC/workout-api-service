from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    """Customise how the User model is displayed and managed in the Django admin (i.e., the admin interface HTML).

    This extends Django's built-in UserAdmin so we inherit the default authentication behaviour while adapting the
    interface for our email-based custom user model.
    """

    ordering = ["id"]
    list_display = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
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


class WorkoutExerciseInline(admin.TabularInline):
    """Display WorkoutExercise rows inside the Workout admin page."""

    model = models.WorkoutExercise
    extra = 0


class WorkoutAdmin(admin.ModelAdmin):
    """Customise the Workout admin page."""

    inlines = [WorkoutExerciseInline]
    list_display = ["id", "title", "user", "duration_minutes"]


class WorkoutExerciseAdmin(admin.ModelAdmin):
    """Customise the WorkoutExercise admin list view."""

    list_display = [
        "id",
        "workout",
        "exercise",
        "order",
        "sets",
        "reps",
        "rest_seconds",
    ]
    list_filter = ["workout", "exercise"]
    ordering = ["workout", "order"]


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Workout, WorkoutAdmin)
admin.site.register(models.Tag)
admin.site.register(models.Exercise)
admin.site.register(models.WorkoutExercise, WorkoutExerciseAdmin)
