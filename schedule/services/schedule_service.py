from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from django.db import transaction
from ..models import Group, Lesson, Gap, Person

class ScheduleService:
    """Сервис для работы с расписанием"""
    
    @staticmethod
    def get_lessons_for_group(group: Group, start_date: date, end_date: date) -> List[Dict]:
        """Получить занятия для группы за период"""
        lessons = Lesson.objects.filter(groups=group)
        
        result = []
        current_date = start_date
        
        while current_date <= end_date:
            for lesson in lessons:
                for expr in lesson.temporal_expressions:
                    if ScheduleService._matches_date(expr, current_date):
                        result.append({
                            'lesson': lesson,
                            'date': current_date.isoformat(),
                            'expression': expr
                        })
            current_date += timedelta(days=1)
        
        return result
    
    @staticmethod
    def _matches_date(expr: Dict, date: date) -> bool:
        """Проверить соответствие выражения дате"""
        expr_type = expr.get('type')
        
        if expr_type == 'onetime':
            expr_date = expr.get('startTimepoint', '').split('T')[0]
            return expr_date == date.isoformat()
        
        elif expr_type == 'weekly':
            start = expr.get('startTimepoint', '').split('T')[0]
            
            expr_day = datetime.strptime(start, '%Y-%m-%d').weekday()
            target_day = date.weekday()
            
            if expr_day != target_day:
                return False
            
            valid_from = expr.get('validFrom', start)
            valid_to = expr.get('validTo', '9999-12-31')
            
            if date.isoformat() < valid_from or date.isoformat() > valid_to:
                return False
            
            return True
        
        return False
    
    @staticmethod
    @transaction.atomic
    def apply_modification(lesson: Lesson, change_type: str, **kwargs) -> Gap:
        """Применить изменение к занятию"""
        gap = Gap.objects.create(
            applies_to=lesson,
            short_name=f"{change_type.capitalize()} {lesson.short_name}",
            reasons=[{
                'type': change_type,
                'notes': kwargs.get('reason', ''),
            }],
            resolutions=[{
                'type': change_type,
                'notes': kwargs.get('notes', ''),
            }]
        )
        
        if change_type == 'substitution':
            new_lesson = Lesson.objects.create(
                type='lesson',
                short_name=f"Замена {lesson.short_name}",
                long_name=f"Замена: {lesson.long_name}",
                course=kwargs.get('course', lesson.course),
                classification='substitution',
                temporal_expressions=lesson.temporal_expressions,
                lesson_type=lesson.lesson_type,
                is_online=lesson.is_online,
            )
            new_lesson.groups.set(lesson.groups.all())
            new_lesson.rooms.set(lesson.rooms.all())
            
            if kwargs.get('teacher'):
                new_lesson.attendees.set([kwargs['teacher']])
            else:
                new_lesson.attendees.set(lesson.attendees.all())
            
            gap.resolutions = [{
                'type': 'substitution',
                'notes': kwargs.get('notes', ''),
                'realizedBy': {'refType': 'lesson', 'refId': new_lesson.id}
            }]
            gap.save()
        
        elif change_type == 'reschedule':
            new_lesson = Lesson.objects.create(
                type='lesson',
                short_name=f"Перенос {lesson.short_name}",
                long_name=f"Перенос: {lesson.long_name}",
                course=lesson.course,
                classification='additional',
                temporal_expressions=kwargs.get('expressions', lesson.temporal_expressions),
                lesson_type=lesson.lesson_type,
                is_online=lesson.is_online,
            )
            new_lesson.groups.set(lesson.groups.all())
            new_lesson.rooms.set(lesson.rooms.all())
            new_lesson.attendees.set(lesson.attendees.all())
            
            gap.resolutions = [{
                'type': 'reschedule',
                'notes': kwargs.get('notes', ''),
                'realizedBy': {'refType': 'lesson', 'refId': new_lesson.id}
            }]
            gap.save()
        
        elif change_type == 'cancellation':
            gap.resolutions = [{
                'type': 'cancellation',
                'message': kwargs.get('message', 'Занятие отменено'),
                'notes': kwargs.get('notes', ''),
            }]
            gap.save()
        
        return gap
    
    @staticmethod
    def get_current_lesson(lesson: Lesson) -> Optional[Lesson]:
        """Получить актуальное состояние занятия"""
        gaps = Gap.objects.filter(applies_to=lesson).order_by('-created_at')
        
        if not gaps:
            return lesson
        
        latest_gap = gaps.first()
        if not latest_gap.resolutions:
            return lesson
        
        last_resolution = latest_gap.resolutions[-1]
        resolution_type = last_resolution.get('type')
        
        if resolution_type == 'cancellation':
            return None
        
        elif resolution_type in ['substitution', 'reschedule']:
            ref_data = last_resolution.get('realizedBy', {})
            if ref_data.get('refType') == 'lesson':
                try:
                    return Lesson.objects.get(id=ref_data['refId'])
                except Lesson.DoesNotExist:
                    return lesson
        
        return lesson
    
    @staticmethod
    def get_modification_history(lesson: Lesson) -> List[Dict]:
        """Получить историю изменений занятия"""
        gaps = Gap.objects.filter(applies_to=lesson).order_by('created_at')
        
        history = []
        for gap in gaps:
            history.append({
                'date': gap.created_at.isoformat(),
                'type': gap.resolutions[-1].get('type') if gap.resolutions else 'none',
                'reasons': gap.reasons,
                'resolutions': gap.resolutions,
            })
        
        return history