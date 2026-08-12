from django.contrib import admin
from django.utils.html import format_html
from .models import *

class BaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name', 'long_name', 'color_preview']
    search_fields = ['short_name', 'long_name', 'id']
    
    def color_preview(self, obj):
        return format_html('<span style="background-color: {}; padding: 2px 10px; border-radius: 3px;">&nbsp;</span>', obj.color)
    color_preview.short_description = 'Цвет'

@admin.register(Building)
class BuildingAdmin(BaseAdmin):
    list_display = ['id', 'short_name', 'long_name', 'color_preview']
    search_fields = ['short_name', 'long_name']

@admin.register(Subject)
class SubjectAdmin(BaseAdmin):
    pass

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'short_name', 'email']
    search_fields = ['full_name', 'short_name', 'email']

@admin.register(GroupType)
class GroupTypeAdmin(BaseAdmin):
    pass

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1
    autocomplete_fields = ['person', 'role']
    fields = ['person', 'role', 'valid_from', 'valid_to']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name', 'long_name', 'course_number']
    list_filter = ['course_number']
    search_fields = ['short_name', 'group_number']
    inlines = [GroupMembershipInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('short_name', 'long_name', 'description', 'color', 'group_type')
        }),
        ('Информация о группе', {
            'fields': ('course_number', 'group_number', 'faculty', 'specialty')
        }),
        ('Дополнительно', {
            'fields': ('valid_from', 'valid_to', 'metadata'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PersonRole)
class PersonRoleAdmin(BaseAdmin):
    pass

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'building', 'capacity', 'floor', 'is_computer_class']
    list_filter = ['building', 'is_computer_class', 'is_lecture_hall', 'floor']
    search_fields = ['building_number', 'room_number']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Аудитория'

@admin.register(CourseType)
class CourseTypeAdmin(BaseAdmin):
    pass

class CourseAttendanceInline(admin.TabularInline):
    model = CourseAttendance
    extra = 1
    autocomplete_fields = ['person', 'role']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name', 'subject', 'course_no']
    list_filter = ['subject', 'course_type']
    filter_horizontal = ['groups']
    inlines = [CourseAttendanceInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('short_name', 'long_name', 'description', 'color', 'subject', 'course_type')
        }),
        ('Детали', {
            'fields': ('course_no', 'course_url')
        }),
        ('Дополнительно', {
            'fields': ('valid_from', 'valid_to', 'metadata'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TimeFrame)
class TimeFrameAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name', 'long_name']

class LessonAttendanceInline(admin.TabularInline):
    model = LessonAttendance
    extra = 1
    autocomplete_fields = ['person', 'role']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name', 'course', 'get_groups_display', 'get_rooms_display', 'classification']
    list_filter = ['classification', 'lesson_type', 'is_online', 'course']
    search_fields = ['short_name', 'long_name']
    filter_horizontal = ['groups', 'rooms']
    inlines = [LessonAttendanceInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('short_name', 'long_name', 'notes', 'color', 'course')
        }),
        ('Расписание', {
            'fields': ('temporal_expressions', 'classification', 'lesson_type')
        }),
        ('Формат', {
            'fields': ('is_online', 'zoom_link')
        }),
        ('Дополнительно', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def get_groups_display(self, obj):
        return obj.get_groups_display()
    get_groups_display.short_description = 'Группы'
    
    def get_rooms_display(self, obj):
        return obj.get_rooms_display()
    get_rooms_display.short_description = 'Аудитории'

@admin.register(Gap)
class GapAdmin(admin.ModelAdmin):
    list_display = ['id', 'applies_to', 'short_name', 'get_resolution_type', 'is_cancellation', 'is_substitution']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_resolution_type(self, obj):
        return obj.get_resolution_type()
    get_resolution_type.short_description = 'Тип изменения'
    
    def is_cancellation(self, obj):
        return obj.is_cancellation()
    is_cancellation.boolean = True
    is_cancellation.short_description = 'Отмена'
    
    def is_substitution(self, obj):
        return obj.is_substitution()
    is_substitution.boolean = True
    is_substitution.short_description = 'Замена'

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name', 'holiday_type']
    list_filter = ['holiday_type']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name']
    filter_horizontal = ['groups', 'attendees', 'rooms']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_description', 'priority']
    list_filter = ['priority']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_name']
    filter_horizontal = ['groups', 'attendees', 'rooms']