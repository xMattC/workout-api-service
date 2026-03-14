from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    """Customise how the User model is displayed and managed in the Django admin.

    This extends Django's built-in UserAdmin so we inherit the default authentication behaviour while adapting the
    interface for our email-based custom user model.
    """

    ordering = ["id"]  # Order users by their database ID in the admin list view
    list_display = ["email", "name"]  # Columns displayed on the admin users list page
    fieldsets = (  # Layout of fields shown on the "edit user" page
        (None, {"fields": ("email", "password")}),  # Basic user credentials
        (  # Permission-related fields controlling admin access and privileges
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),  # Read-only metadata about the user account
    )
    readonly_fields = ["last_login"]  # Fields that should be displayed but not editable in the admin form
    add_fieldsets = (  # Layout of fields shown when creating a new user in admin
        (
            None,
            {
                "classes": ("wide",),  # Apply Django's wide admin form styling
                "fields": (  # Fields required when creating a new user
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


admin.site.register(models.User, UserAdmin)
