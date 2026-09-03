from datetime import datetime, date, timedelta

from django.db import transaction
from django.utils import timezone

from ..models import Group, Lesson, Gap, Person
from ..datetime_utils import parse_iso_datetime, parse_iso_date, to_iso_string, normalize_temporal_expression, validate_temporal_expressions


class ScheduleService:
    """Сервис для работы с расписанием"""

    @staticmethod
    def get_lessons_for_group(
        group: Group,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
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
                            'date': to_iso_string(current_date),
                            'expression': normalize_temporal_expression(expr),
                        })
            current_date += timedelta(days=1)

        return result

    @staticmethod
    def _matches_date(expr: dict, target_date: date) -> bool:
        """Проверить соответствие выражения дате."""
        expr_type = expr.get('type')

        if expr_type == 'onetime':
            try:
                start_dt = parse_iso_datetime(
                    expr.get('startTimepoint'),
                    'startTimepoint',
                )
                local_dt = timezone.localtime(start_dt)
                return local_dt.date() == target_date
            except ValueError:
                return False

        if expr_type == 'weekly':
            try:
                start_dt = parse_iso_datetime(
                    expr.get('startTimepoint'),
                    'startTimepoint',
                )
                local_dt = timezone.localtime(start_dt)
            except ValueError:
                return False

            if local_dt.weekday() != target_date.weekday():
                return False

            valid_from_raw = expr.get('validFrom')
            valid_to_raw = expr.get('validTo')

            if valid_from_raw:
                try:
                    valid_from_date = parse_iso_date(valid_from_raw, 'validFrom')
                    if valid_from_date and target_date < valid_from_date:
                        return False
                except ValueError:
                    pass

            if valid_to_raw:
                try:
                    valid_to_date = parse_iso_date(valid_to_raw, 'validTo')
                    if valid_to_date and target_date > valid_to_date:
                        return False
                except ValueError:
                    pass

            return True

        return False

    @staticmethod
    @transaction.atomic
    def apply_modification(lesson: Lesson, change_type: str, **kwargs: object) -> Gap:
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
                temporal_expressions=validate_temporal_expressions(lesson.temporal_expressions,'lesson.temporal_expressions'),
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
                'realizedBy': {'refType': 'lesson', 'refId': str(new_lesson.id)}
            }]
            gap.save()

        elif change_type == 'reschedule':
            new_lesson = Lesson.objects.create(
                type='lesson',
                short_name=f"Перенос {lesson.short_name}",
                long_name=f"Перенос: {lesson.long_name}",
                course=lesson.course,
                classification='additional',
                temporal_expressions=validate_temporal_expressions(kwargs.get('expressions', lesson.temporal_expressions),'temporal_expressions'),
                lesson_type=lesson.lesson_type,
                is_online=lesson.is_online,
            )
            new_lesson.groups.set(lesson.groups.all())
            new_lesson.rooms.set(lesson.rooms.all())
            new_lesson.attendees.set(lesson.attendees.all())

            gap.resolutions = [{
                'type': 'reschedule',
                'notes': kwargs.get('notes', ''),
                'realizedBy': {'refType': 'lesson', 'refId': str(new_lesson.id)}
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
    @transaction.atomic
    def apply_change_by_ids(
        lesson_id: str,
        change_type: str | None,
        teacher_id: str | None = None,
        reason: str = '',
        notes: str = '',
        message: str = 'Занятие отменено',
        expressions: list | None = None,
    ) -> Gap:
        """
        Применить изменение к занятию по его ID.
        Бросает Lesson.DoesNotExist, Person.DoesNotExist или ValueError.
        """
        if change_type not in {'cancellation', 'substitution', 'reschedule'}:
            raise ValueError(
                'Укажите тип изменения (cancellation/substitution/reschedule)'
            )

        lesson = Lesson.objects.get(id=lesson_id)

        kwargs: dict = {
            'reason': reason,
            'notes': notes,
        }

        if change_type == 'substitution' and teacher_id:
            kwargs['teacher'] = Person.objects.get(id=teacher_id)

        if change_type == 'reschedule' and expressions:
            kwargs['expressions'] = validate_temporal_expressions(expressions, 'expressions')

        if change_type == 'cancellation':
            kwargs['message'] = message

        return ScheduleService.apply_modification(lesson, change_type, **kwargs)

    @staticmethod
    def get_current_lesson(lesson: Lesson) -> Lesson | None:
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
    def get_modification_history(lesson: Lesson) -> list[dict]:
        """Получить историю изменений занятия"""
        gaps = Gap.objects.filter(applies_to=lesson).order_by('created_at')

        history = []
        for gap in gaps:
            history.append({
                'date': to_iso_string(gap.created_at),
                'type': gap.resolutions[-1].get('type') if gap.resolutions else 'none',
                'reasons': gap.reasons,
                'resolutions': gap.resolutions,
            })

        return history