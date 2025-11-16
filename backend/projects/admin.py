from django.contrib import admin
from .models import Project, Stage

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "start_date", "end_date")
    search_fields = ("title",)
    list_filter = ("status",)
    filter_horizontal = ("members",)

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("title", "project")
    search_fields = ("title",)