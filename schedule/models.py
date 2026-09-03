from django.db import models
import uuid

def generate_id() -> str:
    return str(uuid.uuid4())

class BaseModel(models.Model):
    id = models.CharField(max_length=100, primary_key=True, default=generate_id, editable=False)
    short_name = models.CharField('Краткое название', max_length=100)
    long_name = models.CharField('Полное название', max_length=200, blank=True)
    description = models.TextField('Описание', blank=True)
    color = models.CharField('Цвет', max_length=7, default='#4A90D9')
    metadata = models.JSONField('Дополнительные данные', default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def __str__(self) -> str:
        return self.short_name

class Building(BaseModel):
    """Корпус"""
    
    class Meta:
        verbose_name = 'Корпус'
        verbose_name_plural = 'Корпуса'
        ordering = ['short_name']

class Subject(BaseModel):
    """Предмет"""
    
    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'

class Person(BaseModel):
    """Человек (преподаватель, студент)"""
    full_name = models.CharField('Полное имя', max_length=200)
    family_name = models.CharField('Фамилия', max_length=100, blank=True)
    given_name = models.CharField('Имя', max_length=100, blank=True)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'
        ordering = ['family_name', 'given_name']
    
    def __str__(self):
        return self.full_name or self.short_name

class GroupType(BaseModel):
    """Тип группы"""
    
    class Meta:
        verbose_name = 'Тип группы'
        verbose_name_plural = 'Типы групп'

class Group(BaseModel):
    """Группа студентов"""
    group_type = models.ForeignKey(GroupType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Тип группы')
    members = models.ManyToManyField(Person, through='GroupMembership', related_name='groups', verbose_name='Участники')
    valid_from = models.DateField('Действительно с', null=True, blank=True)
    valid_to = models.DateField('Действительно по', null=True, blank=True)
    
    course_number = models.CharField('Номер курса', max_length=10, blank=True, help_text='Например: 1, 2, 3, 4')
    group_number = models.CharField('Номер группы', max_length=20, blank=True, help_text='Например: 22ИП2б')
    faculty = models.CharField('Факультет', max_length=100, blank=True)
    specialty = models.CharField('Специальность', max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['course_number', 'short_name']
    
    def __str__(self):
        return self.short_name

class GroupMembership(models.Model):
    """Участие человека в группе"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='Человек')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа')
    role = models.ForeignKey('PersonRole', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Роль')
    valid_from = models.DateField('Действительно с', null=True, blank=True)
    valid_to = models.DateField('Действительно по', null=True, blank=True)
    
    class Meta:
        unique_together = ['person', 'group']
        verbose_name = 'Участие в группе'
        verbose_name_plural = 'Участия в группах'
    
    def __str__(self):
        return f"{self.person} в {self.group}"

class PersonRole(BaseModel):
    """Роль человека"""
    
    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

class Room(BaseModel):
    """Аудитория (например, 1-237)"""
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Корпус', related_name='rooms')
    building_number = models.CharField('Номер корпуса', max_length=10, blank=True, help_text='Например: 1')
    room_number = models.CharField('Номер аудитории', max_length=20, blank=True, help_text='Например: 237')
    capacity = models.PositiveIntegerField('Вместимость', null=True, blank=True)
    floor = models.PositiveIntegerField('Этаж', null=True, blank=True)
    is_computer_class = models.BooleanField('Компьютерный класс', default=False)
    is_lecture_hall = models.BooleanField('Лекционный зал', default=False)
    
    class Meta:
        verbose_name = 'Аудитория'
        verbose_name_plural = 'Аудитории'
        ordering = ['building_number', 'room_number']
    
    def __str__(self):
        return self.full_name
    
    @property
    def full_name(self) -> str:
        """Возвращает полное название в формате 1-237"""
        if self.building_number and self.room_number:
            return f"{self.building_number}-{self.room_number}"
        return self.short_name

class CourseType(BaseModel):
    """Тип курса"""
    
    class Meta:
        verbose_name = 'Тип курса'
        verbose_name_plural = 'Типы курсов'

class Course(BaseModel):
    """Курс (дисциплина)"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='Предмет', related_name='courses')
    course_no = models.CharField('Номер курса', max_length=20, blank=True)
    course_type = models.ForeignKey(CourseType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Тип курса')
    groups = models.ManyToManyField(Group, related_name='courses', blank=True, verbose_name='Группы')
    attendees = models.ManyToManyField(Person, through='CourseAttendance', related_name='courses', verbose_name='Участники')
    valid_from = models.DateField('Действительно с', null=True, blank=True)
    valid_to = models.DateField('Действительно по', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['subject__short_name', 'short_name']
    
    def __str__(self):
        return f"{self.short_name} ({self.subject.short_name})"

class CourseAttendance(models.Model):
    """Посещаемость курса"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='Человек')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    role = models.ForeignKey(PersonRole, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Роль')
    
    class Meta:
        unique_together = ['person', 'course']
        verbose_name = 'Посещение курса'
        verbose_name_plural = 'Посещения курсов'

class TimeFrame(BaseModel):
    """Временной каркас (расписание звонков)"""
    scope_of_week = models.JSONField('Дни недели', default=list, help_text='["mon", "tue", ...]')
    time_slots = models.JSONField('Временные слоты', default=list, help_text='[{"shortLabel": "1", "startTime": "08:00", ...}]')
    
    class Meta:
        verbose_name = 'Временной каркас'
        verbose_name_plural = 'Временные каркасы'

class ScheduleElement(BaseModel):
    """Базовый элемент расписания"""
    ELEMENT_TYPES = [
        ('lesson', 'Занятие'),
        ('activity', 'Мероприятие'),
        ('event', 'Событие'),
        ('supervision', 'Надзор'),
        ('gap', 'Пробел'),
        ('holiday', 'Каникулы'),
        ('announcement', 'Объявление'),
    ]
    
    CLASSIFICATIONS = [
        ('scheduled', 'Запланированное'),
        ('additional', 'Дополнительное'),
        ('substitution', 'Замена'),
    ]
    
    type = models.CharField('Тип', max_length=20, choices=ELEMENT_TYPES)
    short_name = models.CharField('Краткое название', max_length=100, blank=True)
    long_name = models.CharField('Полное название', max_length=200, blank=True)
    notes = models.TextField('Примечания', blank=True)
    color = models.CharField('Цвет', max_length=7, default='#4A90D9')
    classification = models.CharField('Классификация', max_length=20, choices=CLASSIFICATIONS, default='scheduled')
    temporal_expressions = models.JSONField('Временные выражения', default=list)
    metadata = models.JSONField('Дополнительные данные', default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Элемент расписания'
        verbose_name_plural = 'Элементы расписания'
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.short_name or self.id}"

class Lesson(ScheduleElement):
    """Занятие"""
    LESSON_TYPES = [
        ('lecture', 'Лекция'),
        ('practice', 'Практика'),
        ('lab', 'Лабораторная'),
        ('seminar', 'Семинар'),
        ('exam', 'Экзамен'),
        ('test', 'Зачет'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс', related_name='lessons')
    groups = models.ManyToManyField(Group, related_name='lessons', blank=True, verbose_name='Группы')
    attendees = models.ManyToManyField(Person, through='LessonAttendance', related_name='lessons', verbose_name='Участники')
    rooms = models.ManyToManyField(Room, related_name='lessons', blank=True, verbose_name='Аудитории')
    
    lesson_type = models.CharField('Тип занятия', max_length=50, blank=True, choices=LESSON_TYPES)
    is_online = models.BooleanField('Онлайн', default=False)
    zoom_link = models.URLField('Ссылка на Zoom', blank=True)
    
    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['temporal_expressions']
    
    def __str__(self):
        groups_str = ", ".join([g.short_name for g in self.groups.all()])
        return f"{self.short_name} ({groups_str})"
    
    def get_groups_display(self) -> str:
        return ", ".join([g.short_name for g in self.groups.all()])
    
    def get_rooms_display(self) -> str:
        return ", ".join([room.full_name for room in self.rooms.all()])
    
    def get_teachers_display(self) -> str:
        return ", ".join([p.full_name for p in self.attendees.all()])

class LessonAttendance(models.Model):
    """Участие в занятии"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Занятие')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name='Человек')
    role = models.ForeignKey(PersonRole, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Роль')
    
    class Meta:
        unique_together = ['lesson', 'person']
        verbose_name = 'Участие в занятии'
        verbose_name_plural = 'Участия в занятиях'

class Gap(ScheduleElement):
    """Пробел в расписании (изменение: отмена, замена, перенос)"""
    applies_to = models.ForeignKey(ScheduleElement, on_delete=models.CASCADE, verbose_name='Применяется к', related_name='gaps')
    reasons = models.JSONField('Причины', default=list, help_text='Почему произошло изменение')
    resolutions = models.JSONField('Решения', default=list, help_text='Что было сделано')
    
    class Meta:
        verbose_name = 'Пробел'
        verbose_name_plural = 'Пробелы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Пробел для {self.applies_to}"
    
    def is_cancellation(self) -> bool:
        return self.resolutions and self.resolutions[-1].get('type') == 'cancellation'
    
    def is_substitution(self) -> bool:
        return self.resolutions and self.resolutions[-1].get('type') == 'substitution'
    
    def is_reschedule(self) -> bool:
        return self.resolutions and self.resolutions[-1].get('type') == 'reschedule'
    
    def get_resolution_type(self) -> str | None:
        if self.resolutions:
            return self.resolutions[-1].get('type')
        return None

class Holiday(ScheduleElement):
    """Каникулы/праздники"""
    HOLIDAY_TYPES = [
        ('public', 'Государственный'),
        ('school', 'Школьные'),
        ('custom', 'Другие'),
    ]
    holiday_type = models.CharField('Тип', max_length=20, choices=HOLIDAY_TYPES)
    
    class Meta:
        verbose_name = 'Каникулы'
        verbose_name_plural = 'Каникулы'

class Activity(ScheduleElement):
    """Мероприятие"""
    groups = models.ManyToManyField(Group, related_name='activities', blank=True, verbose_name='Группы')
    attendees = models.ManyToManyField(Person, related_name='activities', blank=True, verbose_name='Участники')
    rooms = models.ManyToManyField(Room, related_name='activities', blank=True, verbose_name='Аудитории')
    
    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

class Announcement(ScheduleElement):
    """Объявление"""
    short_description = models.CharField('Краткое описание', max_length=200)
    long_description = models.TextField('Полное описание', blank=True)
    priority = models.CharField('Приоритет', max_length=20, 
                              choices=[('important', 'Важно'), ('alarm', 'Срочно')], blank=True)
    
    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'

class Event(ScheduleElement):
    """Событие"""
    groups = models.ManyToManyField(Group, related_name='events', blank=True, verbose_name='Группы')
    attendees = models.ManyToManyField(Person, related_name='events', blank=True, verbose_name='Участники')
    rooms = models.ManyToManyField(Room, related_name='events', blank=True, verbose_name='Аудитории')
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'