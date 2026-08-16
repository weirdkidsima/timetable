import json
from argparse import ArgumentParser
from django.core.management.base import BaseCommand
from schedule.services.importer import OpenT8Importer

class Command(BaseCommand):
    help = 'Import data from OpenT8 JSON format'

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to OpenT8 JSON file',
        )

    def handle(self, *args: object, **options: object) -> None:
        file_path = str(options['file_path'])

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            importer = OpenT8Importer(data)
            stats = importer.import_all()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported:\n'
                    f'  Created: {stats["created"]}\n'
                    f'  Updated: {stats["updated"]}\n'
                    f'  Errors: {stats["errors"]}'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))