import csv
from django.core.management.base import BaseCommand
from core.models import Exercise

class Command(BaseCommand):
    help = 'Seed database from CSV'

    def handle(self, *args, **kwargs):
        with open('path/to/your_file.csv', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                Exercise.objects.create(
                    name=row['name'],
                    description=row['description'],
                    category=row['category'],
                    is_public = True
                )

        self.stdout.write(self.style.SUCCESS('Data successfully seeded!'))