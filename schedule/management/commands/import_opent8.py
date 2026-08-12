from django.core.management.base import BaseCommand
from schedule.services.importer import OpenT8Importer
import json

class Command(BaseCommand):
    help = 'Import data from OpenT8 JSON format'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to OpenT8 JSON file')
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            importer = OpenT8Importer(data)
            stats = importer.import_all()
            self.stdout.write(self.style.SUCCESS(
                f'Successfully imported:\n  Created: {stats["created"]}\n  Updated: {stats["updated"]}\n  Errors: {stats["errors"]}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))