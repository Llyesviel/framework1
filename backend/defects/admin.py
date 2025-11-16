from django.contrib import admin
from .models import Defect, Attachment, Comment, StatusHistory

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "stage", "status", "priority", "performer", "deadline")
    search_fields = ("title", "description")
    list_filter = ("status", "priority", "project")

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("defect", "uploaded_at")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("defect", "author", "created_at")

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("defect", "old_status", "new_status", "changed_by", "changed_at")