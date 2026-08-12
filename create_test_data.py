import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_system.settings')
django.setup()

from schedule.models import *

print("=" * 50)
print("Создание тестовых данных для вуза")
print("=" * 50)

# Корпуса
building1 = Building.objects.create(
    id="building-1",
    short_name="1",
    long_name="Первый корпус"
)
building2 = Building.objects.create(
    id="building-2",
    short_name="2",
    long_name="Второй корпус"
)
building3 = Building.objects.create(
    id="building-3",
    short_name="3",
    long_name="Третий корпус"
)

print("Корпуса созданы")

# Аудитории
Room.objects.create(
    id="room-1-237",
    short_name="1-237",
    long_name="Аудитория 1-237",
    building=building1,
    building_number="1",
    room_number="237",
    capacity=30,
    floor=2
)
Room.objects.create(
    id="room-1-101",
    short_name="1-101",
    long_name="Аудитория 1-101",
    building=building1,
    building_number="1",
    room_number="101",
    capacity=25,
    floor=1
)
Room.objects.create(
    id="room-2-301",
    short_name="2-301",
    long_name="Аудитория 2-301",
    building=building2,
    building_number="2",
    room_number="301",
    capacity=40,
    floor=3
)
Room.objects.create(
    id="room-2-201",
    short_name="2-201",
    long_name="Аудитория 2-201",
    building=building2,
    building_number="2",
    room_number="201",
    capacity=35,
    floor=2
)
Room.objects.create(
    id="room-3-101",
    short_name="3-101",
    long_name="Аудитория 3-101",
    building=building3,
    building_number="3",
    room_number="101",
    capacity=50,
    floor=1
)

print("Аудитории созданы")

# Предметы
Subject.objects.create(
    id="subject-db",
    short_name="БД",
    long_name="Базы данных"
)
Subject.objects.create(
    id="subject-python",
    short_name="Python",
    long_name="Программирование на Python"
)
Subject.objects.create(
    id="subject-web",
    short_name="Web",
    long_name="Веб-технологии"
)
Subject.objects.create(
    id="subject-math",
    short_name="Матан",
    long_name="Математический анализ"
)

print("Предметы созданы")

# Преподаватели
teacher1 = Person.objects.create(
    id="teacher-ivanov",
    short_name="Иванов И.И.",
    full_name="Иванов Иван Иванович"
)
teacher2 = Person.objects.create(
    id="teacher-petrov",
    short_name="Петров П.П.",
    full_name="Петров Петр Петрович"
)
teacher3 = Person.objects.create(
    id="teacher-sidorova",
    short_name="Сидорова А.С.",
    full_name="Сидорова Анна Сергеевна"
)

print("Преподаватели созданы")

# Группы
group1 = Group.objects.create(
    id="group-pi101",
    short_name="22ИП1",
    long_name="Группа 22ИП1",
    course_number="2",
    group_number="22ИП1",
    faculty="Факультет информационных технологий"
)
group2 = Group.objects.create(
    id="group-pi102",
    short_name="22ИП2б",
    long_name="Группа 22ИП2б",
    course_number="2",
    group_number="22ИП2б",
    faculty="Факультет информационных технологий"
)
group3 = Group.objects.create(
    id="group-pi201",
    short_name="21ИП1",
    long_name="Группа 21ИП1",
    course_number="3",
    group_number="21ИП1",
    faculty="Факультет информационных технологий"
)

print("✓ Группы созданы")

# Курсы
course_db = Course.objects.create(
    id="course-db",
    short_name="БД-22ИП1",
    long_name="Базы данных для 22ИП1",
    subject=Subject.objects.get(id="subject-db")
)
course_db.groups.add(group1)

course_python = Course.objects.create(
    id="course-python",
    short_name="Python-22ИП2б",
    long_name="Python для 22ИП2б",
    subject=Subject.objects.get(id="subject-python")
)
course_python.groups.add(group2)

course_web = Course.objects.create(
    id="course-web",
    short_name="Web-21ИП1",
    long_name="Веб-технологии для 21ИП1",
    subject=Subject.objects.get(id="subject-web")
)
course_web.groups.add(group3)

print("✓ Курсы созданы")

# Занятия
lesson1 = Lesson.objects.create(
    id="lesson-db-1",
    type="lesson",
    short_name="БД",
    long_name="Базы данных (лекция)",
    course=course_db,
    classification="scheduled",
    lesson_type="lecture",
    temporal_expressions=[{
        "type": "weekly",
        "startTimepoint": "2024-09-02T10:00:00Z",
        "endTimepoint": "2024-09-02T11:30:00Z",
        "validFrom": "2024-09-01",
        "validTo": "2024-12-31"
    }]
)
lesson1.groups.add(group1)
lesson1.rooms.add(Room.objects.get(id="room-1-237"))
lesson1.attendees.add(teacher1)

lesson2 = Lesson.objects.create(
    id="lesson-python-1",
    type="lesson",
    short_name="Python",
    long_name="Программирование на Python (практика)",
    course=course_python,
    classification="scheduled",
    lesson_type="practice",
    temporal_expressions=[{
        "type": "weekly",
        "startTimepoint": "2024-09-03T14:00:00Z",
        "endTimepoint": "2024-09-03T15:30:00Z",
        "validFrom": "2024-09-01",
        "validTo": "2024-12-31"
    }]
)
lesson2.groups.add(group2)
lesson2.rooms.add(Room.objects.get(id="room-2-301"))
lesson2.attendees.add(teacher2)

lesson3 = Lesson.objects.create(
    id="lesson-web-1",
    type="lesson",
    short_name="Web",
    long_name="Веб-технологии (лекция)",
    course=course_web,
    classification="scheduled",
    lesson_type="lecture",
    temporal_expressions=[{
        "type": "weekly",
        "startTimepoint": "2024-09-04T10:00:00Z",
        "endTimepoint": "2024-09-04T11:30:00Z",
        "validFrom": "2024-09-01",
        "validTo": "2024-12-31"
    }]
)
lesson3.groups.add(group3)
lesson3.rooms.add(Room.objects.get(id="room-3-101"))
lesson3.attendees.add(teacher3)

print("✓ Занятия созданы")

print("=" * 50)
print("Тестовые данные созданы!")
print("=" * 50)
print(f"Корпуса: {Building.objects.count()}")
print(f"Аудитории: {Room.objects.count()}")
print(f"Предметы: {Subject.objects.count()}")
print(f"Преподаватели: {Person.objects.count()}")
print(f"Группы: {Group.objects.count()}")
print(f"Курсы: {Course.objects.count()}")
print(f"Занятия: {Lesson.objects.count()}")
print("=" * 50)