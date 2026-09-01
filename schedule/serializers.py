from .models import Group

def serialize_group(group: Group) -> dict:
    return {
        'id' : group.id,
        'short_name' : group.short_name,
        'long_name': group.long_name,
        'course_number': group.course_number,
        'faculty': group.faculty,
    }