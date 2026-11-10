from django.contrib import admin
from .models import Project, Task, Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ['name']

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'budget']
    list_display_links = ['name']
    list_editable = ['status']
    search_fields = ['name']
    list_filter = ['status']
    inlines = [TaskInline]
    fieldsets = [
        ('基本信息', {'fields': ['name', 'budget', 'status', 'teams']}),
        ('资料与文档', {'fields': ['body', 'notes', 'settings', 'cover', 'attachment']}),
    ]
    ordloom_fields = {
        'budget': {'precision': 2, 'min': 0},
        'notes': {'rows': 12},
        'settings': {'span': 2},
        'cover': {'max_upload_size_mb': 5},
        'attachment': {'accept': '.pdf,.txt', 'max_upload_size_mb': 20},
    }
