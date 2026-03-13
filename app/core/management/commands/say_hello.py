"""
Custom Django management command example.

This file demonstrates how Django discovers and runs custom CLI commands.

How it works:
    Any Python file placed in:

        <app_name>/management/commands/

    automatically becomes available through the Django CLI using:

        python manage.py <filename>

Example:
    If this file is named:

        say_hello.py

    then the command can be executed with:

        python manage.py say_hello

Execution flow:
    1. Django loads all apps listed in INSTALLED_APPS.
    2. It searches for a `management/commands/` directory inside each app.
    3. Each Python file found there becomes a command.
    4. Django loads the `Command` class and executes its `handle()` method.

Purpose:
    Management commands are commonly used for:

    - database setup tasks
    - cron jobs / scheduled jobs
    - data imports and exports
    - maintenance scripts
    - Docker startup helpers (e.g. wait_for_db)

The `handle()` method is the entry point executed when the command runs.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Hello! This is a custom Django management command.")
