from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Group, Lesson, Gap, Person
from .services.schedule_service import ScheduleService
from .serializers import serialize_group, serialize_group_schedule
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
    
    return JsonResponse({
        'lesson': {
            'id': lesson.id,
            'short_name': lesson.short_name,
            'long_name': lesson.long_name,
        },
        'history': [{
            'date': h['date'],
            'type': h['type'],
            'reasons': h['reasons'],
            'resolutions': h['resolutions'],
        } for h in history]
    })

@csrf_exempt
def apply_change(request: HttpRequest, lesson_id: str) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'Занятие не найдено'}, status=404)
    
    try:
        data = json.loads(request.body)
        change_type = data.get('type')
        
        if not change_type:
            return JsonResponse({'error': 'Укажите тип изменения (cancellation/substitution/reschedule)'}, status=400)
        
        kwargs = {
            'reason': data.get('reason', ''),
            'notes': data.get('notes', ''),
        }
        
        if change_type == 'substitution' and data.get('teacher_id'):
            try:
                teacher = Person.objects.get(id=data['teacher_id'])
                kwargs['teacher'] = teacher
            except Person.DoesNotExist:
                return JsonResponse({'error': 'Преподаватель не найден'}, status=404)
        
        if change_type == 'reschedule' and data.get('expressions'):
            kwargs['expressions'] = data['expressions']
        
        if change_type == 'cancellation':
            kwargs['message'] = data.get('message', 'Занятие отменено')
        
        gap = ScheduleService.apply_modification(lesson, change_type, **kwargs)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Изменение {change_type} применено',
            'gap_id': gap.id
        })
        
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