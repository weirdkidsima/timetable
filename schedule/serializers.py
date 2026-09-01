from .models import Group, Lesson


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
        'date': item['date'],
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


def serialize_group_schedule(
    group: Group,
    start_date: str,
    end_date: str,
    items: list[dict],
) -> dict:
    return {
        'group': group.short_name,
        'start_date': start_date,
        'end_date': end_date,
        'lessons': [serialize_schedule_item(item) for item in items],
    }