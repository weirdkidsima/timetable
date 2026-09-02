from .models import Group, Lesson
from .datetime_utils import to_iso_string


def serialize_group(group: Group) -> dict:
    return {
        'id': group.id,
        'short_name': group.short_name,
        'long_name': group.long_name,
        'course_number': group.course_number,
        'faculty': group.faculty,
    }


def serialize_schedule_item(item: dict) -> dict:
    lesson: Lesson = item['lesson']

    return {
        'date': item['date'], # ИСПРАВИТЬ
        'lesson': {
            'id': lesson.id,
            'short_name': lesson.short_name,
            'long_name': lesson.long_name,
            'lesson_type': lesson.lesson_type,
            'groups': [group.short_name for group in lesson.groups.all()],
            'rooms': [room.full_name for room in lesson.rooms.all()],
            'teachers': [person.full_name for person in lesson.attendees.all()],
            'time': item['expression'],
            'is_online': lesson.is_online,
        },
    }


def serialize_group_schedule(group: Group, start_dt: str, end_dt: str, items: list[dict]) -> dict:
    return {
        'group': group.short_name,
        'start_date': to_iso_string(start_dt),
        'end_date': to_iso_string(end_dt),
        'lessons': [serialize_schedule_item(item) for item in items],
    }

def serialize_lesson_history(lesson: Lesson, history: list[dict]) -> dict:
    return {
        'lesson': {
            'id': lesson.id,
            'short_name': lesson.short_name,
            'long_name': lesson.long_name,
        },
        'history': [
            {
                'date': item['date'],
                'type': item['type'],
                'reasons': item['reasons'],
                'resolutions': item['resolutions'],
            }
            for item in history
        ],
    }