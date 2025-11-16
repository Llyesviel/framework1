from rest_framework import serializers
from .models import Project, Stage

class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ["id", "project", "title", "description"]

class ProjectSerializer(serializers.ModelSerializer):
    stages = StageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "status",
            "members",
            "stages",
        ]