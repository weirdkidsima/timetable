from datetime import date, datetime, time

from django.utils import timezone


ALLOWED_TEMPORAL_TYPES = {
    'onetime',
    'weekly',
}


def parse_iso_datetime(
    value: str | None,
    field_name: str = 'datetime',
    *,
    end_of_day: bool = False,
) -> datetime:
    """
    Парсит дату/время в timezone-aware datetime.

    Поддерживает:
    - 2024-09-01
    - 2024-09-01T10:00:00
    - 2024-09-01T10:00:00Z
    - 2024-09-01T10:00:00+03:00

    Если передана только дата и указан end_of_day=True,
    дата приводится к концу дня.
    """
    if value is None:
        raise ValueError(
            f"Укажите параметр '{field_name}' в формате ISO 8601"
        )

    text = str(value).strip()

    if not text:
        raise ValueError(
            f"Укажите параметр '{field_name}' в формате ISO 8601"
        )

    if text.endswith('Z'):
        text = f"{text[:-1]}+00:00"

    try:
        if len(text) == 10:
            parsed_date = date.fromisoformat(text)
            dt = datetime.combine(
                parsed_date,
                time.max if end_of_day else time.min,
            )
        else:
            dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            f"Неверный формат параметра '{field_name}'. "
            f"Ожидается ISO 8601: YYYY-MM-DD или YYYY-MM-DDTHH:MM:SS±HH:MM"
        ) from exc

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)

    return dt


def parse_iso_date(
    value: str | None,
    field_name: str = 'date',
) -> date | None:
    """
    Парсит дату или datetime и возвращает дату в таймзоне проекта.

    Используется для DateField.
    """
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    dt = parse_iso_datetime(text, field_name)

    return timezone.localtime(dt).date()


def to_iso_string(value: datetime | date | None) -> str | None:
    """
    Возвращает полный ISO 8601 с таймзоной проекта

    Дата без времени приводится к началу дня
    """
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min)

    if timezone.is_naive(value):
        value = timezone.make_aware(value)

    return timezone.localtime(value).isoformat()


def normalize_temporal_expression(expression: dict) -> dict:
    """
    Приводит temporal expression к полному ISO 8601 формату.

    Поддерживает:
    - startTimepoint
    - endTimepoint
    - validFrom
    - validTo
    """
    if not isinstance(expression, dict):
        raise ValueError(
            'Temporal expression должен быть объектом'
        )

    expr_type = expression.get('type')

    if expr_type not in ALLOWED_TEMPORAL_TYPES:
        raise ValueError(
            "Temporal expression должен иметь тип 'onetime' или 'weekly'"
        )

    normalized = dict(expression)

    normalized['startTimepoint'] = to_iso_string(
        parse_iso_datetime(
            normalized.get('startTimepoint'),
            'temporalExpression.startTimepoint',
        )
    )

    normalized['endTimepoint'] = to_iso_string(
        parse_iso_datetime(
            normalized.get('endTimepoint'),
            'temporalExpression.endTimepoint',
        )
    )

    if normalized.get('validFrom'):
        normalized['validFrom'] = to_iso_string(
            parse_iso_datetime(
                normalized.get('validFrom'),
                'temporalExpression.validFrom',
            )
        )
    elif 'validFrom' in normalized:
        normalized.pop('validFrom')

    if normalized.get('validTo'):
        normalized['validTo'] = to_iso_string(
            parse_iso_datetime(
                normalized.get('validTo'),
                'temporalExpression.validTo',
                end_of_day=True,
            )
        )
    elif 'validTo' in normalized:
        normalized.pop('validTo')

    return normalized


def validate_temporal_expressions(
    expressions: list | None,
    field_name: str = 'temporalExpressions',
) -> list[dict]:
    """
    Проверяет список temporal expressions и возвращает нормализованный список
    """
    if expressions is None:
        return []

    if not isinstance(expressions, list):
        raise ValueError(
            f"Параметр '{field_name}' должен быть массивом"
        )

    return [
        normalize_temporal_expression(expression)
        for expression in expressions
    ]