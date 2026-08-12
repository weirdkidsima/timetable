from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/groups/', views.group_list, name='group_list'),
    path('api/groups/<str:group_id>/schedule/', views.group_schedule, name='group_schedule'),
    path('api/lessons/<str:lesson_id>/history/', views.lesson_history, name='lesson_history'),
    path('api/lessons/<str:lesson_id>/apply_change/', views.apply_change, name='apply_change'),
    path('api/import/', views.import_data, name='import_data'),
]