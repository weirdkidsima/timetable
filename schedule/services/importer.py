import json
import re
from datetime import date

from django.db import models, transaction

from ..models import (
    Activity,
    Announcement,
    Building,
    Course,
    Event,
    Gap,
    Group,
    Holiday,
    Lesson,
    Person,
    Room,
    Subject,
    TimeFrame,
)
from ..datetime_utils import parse_iso_date, validate_temporal_expressions


class OpenT8Importer:
    def __init__(self, json_data: dict | str) -> None:
        if isinstance(json_data, dict):
            self.data = json_data
        else:
            self.data = json.loads(json_data)

        self.id_map: dict[str, models.Model] = {}
        self.stats: dict[str, int] = {
            'created': 0,
            'updated': 0,
            'errors': 0,
        }

    def _parse_date_field(self, value: str | None, field_name: str) -> date | None:
        """Парсит дату для DateField. Возвращает None при ошибке."""
        if not value:
            return None
        try:
            return parse_iso_date(value, field_name)
        except ValueError as e:
            self.stats['errors'] += 1
            print(f"Ошибка парсинга даты {field_name}: {e}")
            return None

    def _normalize_temporal_expressions(
        self,
        expressions: list | None,
        element_id: str,
    ) -> list[dict]:
        """Нормализует temporal expressions. Возвращает пустой список при ошибке."""
        if not expressions:
            return []
        try:
            return validate_temporal_expressions(expressions, 'temporalExpressions')
        except ValueError as e:
            self.stats['errors'] += 1
            print(f"Ошибка в temporalExpressions для {element_id}: {e}")
            return []

    @transaction.atomic
    def import_all(self) -> dict[str, int]:
        print("Начинаем импорт данных OpenT8...")

        self._import_buildings()
        self._import_subjects()
        self._import_persons()
        self._import_groups()
        self._import_rooms()
        self._import_courses()
        self._import_time_frames()
        self._import_schedule_elements()

        print(
            f"Импорт завершен. "
            f"Создано: {self.stats['created']}, "
            f"Обновлено: {self.stats['updated']}, "
            f"Ошибок: {self.stats['errors']}"
        )

        return self.stats

    def _save_model(
        self,
        model: type[models.Model],
        data: dict,
        defaults: dict,
    ) -> models.Model | None:
        try:
            obj, created = model.objects.update_or_create(
                id=data['id'],
                defaults=defaults,
            )
            self.stats['created' if created else 'updated'] += 1
            return obj
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Ошибка: {e}")
            return None

    def _import_buildings(self) -> None:
        for data in self.data.get('buildings', []):
            obj = self._save_model(Building, data, {
                'short_name': data.get('shortName', ''),
                'long_name': data.get('longName', ''),
                'description': data.get('description', ''),
                'color': data.get('color', '#4A90D9'),
            })
            if obj:
                self.id_map[f"building:{data['id']}"] = obj

    def _import_subjects(self) -> None:
        for data in self.data.get('subjects', []):
            obj = self._save_model(Subject, data, {
                'short_name': data.get('shortName', ''),
                'long_name': data.get('longName', ''),
                'description': data.get('description', ''),
                'color': data.get('color', '#4A90D9'),
            })
            if obj:
                self.id_map[f"subject:{data['id']}"] = obj

    def _import_persons(self) -> None:
        for data in self.data.get('persons', []):
            name = data.get('name', {})
            obj = self._save_model(Person, data, {
                'short_name': name.get('shortName', data.get('shortName', '')),
                'long_name': name.get('fullName', data.get('longName', '')),
                'full_name': name.get('fullName', ''),
                'family_name': name.get('familyName', ''),
                'given_name': name.get('givenName', ''),
                'email': data.get('email', ''),
            })
            if obj:
                self.id_map[f"person:{data['id']}"] = obj

    def _import_groups(self) -> None:
        for data in self.data.get('groups', []):
            name = data.get('shortName', '')
            course_number = ''

            if name:
                match = re.search(r'(\d+)', name)
                if match:
                    course_number = match.group(1)[0] if len(match.group(1)) > 0 else ''

            obj = self._save_model(Group, data, {
                'short_name': data.get('shortName', ''),
                'long_name': data.get('longName', ''),
                'description': data.get('description', ''),
                'color': data.get('color', '#4A90D9'),
                'course_number': course_number,
                'group_number': data.get('shortName', ''),
                'valid_from': self._parse_date_field(data.get('validFrom'), 'validFrom'),
                'valid_to': self._parse_date_field(data.get('validTo'), 'validTo'),
            })
            if obj:
                self.id_map[f"group:{data['id']}"] = obj

    def _import_rooms(self) -> None:
        for data in self.data.get('rooms', []):
            room_name = data.get('shortName', '')
            building_number = ''
            room_number = ''

            if '-' in room_name:
                parts = room_name.split('-')
                if len(parts) == 2:
                    building_number = parts[0]
                    room_number = parts[1]

            obj = self._save_model(Room, data, {
                'short_name': data.get('shortName', ''),
                'long_name': data.get('longName', ''),
                'description': data.get('description', ''),
                'color': data.get('color', '#4A90D9'),
                'building_number': building_number,
                'room_number': room_number,
                'capacity': data.get('capacity'),
                'floor': data.get('floor'),
            })
            if obj:
                self.id_map[f"room:{data['id']}"] = obj

    def _import_courses(self) -> None:
        for data in self.data.get('courses', []):
            subject = self.id_map.get(
                f"subject:{data.get('subject', {}).get('refId')}"
            )

            obj = self._save_model(Course, data, {
                'short_name': data.get('shortName', ''),
                'long_name': data.get('longName', ''),
                'description': data.get('description', ''),
                'color': data.get('color', '#4A90D9'),
                'subject': subject,
                'course_no': data.get('courseNo', ''),
                'valid_from': self._parse_date_field(data.get('validFrom'), 'validFrom'),
                'valid_to': self._parse_date_field(data.get('validTo'), 'validTo'),
            })
            if obj:
                self.id_map[f"course:{data['id']}"] = obj
                for group_ref in data.get('groups', []):
                    group = self.id_map.get(f"group:{group_ref.get('refId')}")
                    if group:
                        obj.groups.add(group)

    def _import_time_frames(self) -> None:
        for data in self.data.get('timeFrames', []):
            obj = self._save_model(TimeFrame, data, {
                'short_name': data.get('shortName', ''),
                'long_name': data.get('longName', ''),
                'description': data.get('description', ''),
                'scope_of_week': data.get('scopeOfWeek', []),
                'time_slots': data.get('timeSlots', []),
            })
            if obj:
                self.id_map[f"time_frame:{data['id']}"] = obj

    def _import_schedule_elements(self) -> None:
        schedule = self.data.get('schedule', {})
        for data in schedule.get('scheduleElements', []):
            element_type = data.get('type')

            if element_type == 'lesson':
                self._import_lesson(data)
            elif element_type == 'gap':
                self._import_gap(data)
            elif element_type == 'holiday':
                self._import_holiday(data)
            elif element_type == 'activity':
                self._import_activity(data)
            elif element_type == 'announcement':
                self._import_announcement(data)
            elif element_type == 'event':
                self._import_event(data)

    def _import_lesson(self, data: dict) -> None:
        course = self.id_map.get(
            f"course:{data.get('course', {}).get('refId')}"
        )
        element_id = data.get('id', '')

        obj = self._save_model(Lesson, data, {
            'type': 'lesson',
            'short_name': data.get('shortName', ''),
            'long_name': data.get('longName', ''),
            'notes': data.get('notes', ''),
            'color': data.get('color', '#4A90D9'),
            'classification': data.get('classification', 'scheduled'),
            'temporal_expressions': self._normalize_temporal_expressions(
                data.get('temporalExpressions', []),
                element_id,
            ),
            'course': course,
        })
        if obj:
            self.id_map[f"schedule_element:{data['id']}"] = obj
            for group_ref in data.get('groups', []):
                group = self.id_map.get(f"group:{group_ref.get('refId')}")
                if group:
                    obj.groups.add(group)
            for room_ref in data.get('rooms', []):
                room = self.id_map.get(f"room:{room_ref.get('refId')}")
                if room:
                    obj.rooms.add(room)

    def _import_gap(self, data: dict) -> None:
        applies_to = self.id_map.get(
            f"schedule_element:{data.get('appliesTo', {}).get('refId')}"
        )
        element_id = data.get('id', '')

        obj = self._save_model(Gap, data, {
            'type': 'gap',
            'short_name': data.get('shortName', ''),
            'notes': data.get('notes', ''),
            'color': data.get('color', '#4A90D9'),
            'temporal_expressions': self._normalize_temporal_expressions(
                data.get('temporalExpressions', []),
                element_id,
            ),
            'applies_to': applies_to,
            'reasons': data.get('reasons', []),
            'resolutions': data.get('resolutions', []),
        })
        if obj:
            self.id_map[f"schedule_element:{data['id']}"] = obj

    def _import_holiday(self, data: dict) -> None:
        element_id = data.get('id', '')

        obj = self._save_model(Holiday, data, {
            'type': 'holiday',
            'short_name': data.get('shortName', ''),
            'long_name': data.get('longName', ''),
            'notes': data.get('notes', ''),
            'color': data.get('color', '#4A90D9'),
            'temporal_expressions': self._normalize_temporal_expressions(
                data.get('temporalExpressions', []),
                element_id,
            ),
            'holiday_type': data.get('holidayType', 'school'),
        })
        if obj:
            self.id_map[f"schedule_element:{data['id']}"] = obj

    def _import_activity(self, data: dict) -> None:
        element_id = data.get('id', '')

        obj = self._save_model(Activity, data, {
            'type': 'activity',
            'short_name': data.get('shortName', ''),
            'long_name': data.get('longName', ''),
            'notes': data.get('notes', ''),
            'color': data.get('color', '#4A90D9'),
            'temporal_expressions': self._normalize_temporal_expressions(
                data.get('temporalExpressions', []),
                element_id,
            ),
        })
        if obj:
            self.id_map[f"schedule_element:{data['id']}"] = obj

    def _import_announcement(self, data: dict) -> None:
        element_id = data.get('id', '')

        obj = self._save_model(Announcement, data, {
            'type': 'announcement',
            'short_name': data.get('shortName', ''),
            'notes': data.get('notes', ''),
            'color': data.get('color', '#4A90D9'),
            'temporal_expressions': self._normalize_temporal_expressions(
                data.get('temporalExpressions', []),
                element_id,
            ),
            'short_description': data.get('shortDescription', ''),
            'long_description': data.get('longDescription', ''),
            'priority': data.get('priority', ''),
        })
        if obj:
            self.id_map[f"schedule_element:{data['id']}"] = obj

    def _import_event(self, data: dict) -> None:
        element_id = data.get('id', '')

        obj = self._save_model(Event, data, {
            'type': 'event',
            'short_name': data.get('shortName', ''),
            'long_name': data.get('longName', ''),
            'notes': data.get('notes', ''),
            'color': data.get('color', '#4A90D9'),
            'temporal_expressions': self._normalize_temporal_expressions(
                data.get('temporalExpressions', []),
                element_id,
            ),
        })
        if obj:
            self.id_map[f"schedule_element:{data['id']}"] = obj