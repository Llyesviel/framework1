from rest_framework import serializers
from .models import Defect, Attachment, Comment, StatusHistory

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "defect", "file", "uploaded_at"]

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "defect", "author", "text", "created_at"]

class StatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHistory
        fields = ["id", "defect", "old_status", "new_status", "changed_by", "changed_at"]

class DefectSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    status_history = StatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Defect
        fields = [
            "id",
            "project",
            "stage",
            "title",
            "description",
            "priority",
            "status",
            "performer",
            "deadline",
            "created_at",
            "updated_at",
            "attachments",
            "comments",
            "status_history",
        ]