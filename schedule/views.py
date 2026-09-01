from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Group, Lesson, Gap, Person
from .services.schedule_service import ScheduleService
from .serializers import serialize_group, serialize_group_schedule, serialize_lesson_history
import json
from datetime import datetime

def index(request: HttpRequest) -> JsonResponse:
    return JsonResponse({
        'status': 'ok',
        'message': 'OpenT8 Schedule API',
        'endpoints': {
            'admin': '/admin/',
            'api/groups/': 'GET - список групп',
            'api/groups/<id>/schedule/': 'GET - расписание группы',
            'api/lessons/<id>/history/': 'GET - история изменений',
            'api/lessons/<id>/apply_change/': 'POST - применить изменение',
            'api/import/': 'POST - импорт OpenT8 JSON',
        }
    })

def group_list(request: HttpRequest) -> JsonResponse:
    groups = Group.objects.all()
    data = [serialize_group(group) for group in groups]
    return JsonResponse({'groups': data})

def group_schedule(request: HttpRequest, group_id: str) -> JsonResponse:
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Группа не найдена'}, status=404)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return JsonResponse(
            {'error': 'Укажите start_date и end_date в формате YYYY-MM-DD'},
            status=400,
        )

    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)

    lessons = ScheduleService.get_lessons_for_group(group, start, end)

    return JsonResponse(
        serialize_group_schedule(
            group,
            start_date,
            end_date,
            lessons,
        )
    )

def lesson_history(request: HttpRequest, lesson_id: str) -> JsonResponse:
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'Занятие не найдено'}, status=404)

    history = ScheduleService.get_modification_history(lesson)

    return JsonResponse(serialize_lesson_history(lesson, history))

@csrf_exempt
def apply_change(request: HttpRequest, lesson_id: str) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    try:
        data = json.loads(request.body)
        
        gap = ScheduleService.apply_change_by_ids(
            lesson_id=lesson_id,
            change_type=data.get('type'),
            teacher_id=data.get('teacher_id'),
            reason=data.get('reason', ''),
            notes=data.get('notes', ''),
            message=data.get('message', 'Занятие отменено'),
            expressions=data.get('expressions'),
        )

        return JsonResponse({
            'status': 'success',
            'message': f"Изменение {data.get('type')} применено",
            'gap_id': gap.id,
        })
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'Занятие не найдено'}, status=404)
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Преподаватель не найден'}, status=404)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def import_data(request: HttpRequest) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        data = json.loads(request.body)
        from .services.importer import OpenT8Importer
        importer = OpenT8Importer(data)
        stats = importer.import_all()
        return JsonResponse({
            'status': 'ok',
            'stats': stats
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)