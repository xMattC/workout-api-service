# Core Django model utilities
from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,  # Provides password hashing and authentication features
    BaseUserManager,  # Provides helper methods for creating users
    PermissionsMixin,  # Adds permission-related fields (groups, is_superuser, etc.)
)


class UserManager(BaseUserManager):
    """Custom manager for the User model.

    The manager defines how User objects are created. Django calls these methods when creating users via code,
    management commands, or tests.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user.

        The email address is required and used as the login identifier.
        The password is hashed using Django's built-in password system before being stored in the database.
        """
        if not email:
            raise ValueError("User must have an email address.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a superuser.

        A superuser has full administrative permissions and access to the Django admin interface.
        """
        user = self.create_user(email, password)

        # Grant admin site access and full permissions
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for the project.

    This replaces Django's default username-based user model with an email-based authentication system.
    """

    email = models.EmailField(max_length=255, unique=True)  # Primary login identifier
    name = models.CharField(max_length=255)  # Display name for the user
    is_active = models.BooleanField(default=True)  # Determines whether the account is active
    is_staff = models.BooleanField(default=False)  # Allows access to the Django admin interface
    objects = UserManager()  # Attach the custom manager to the model
    USERNAME_FIELD = "email"  # Attach the custom manager to the model
