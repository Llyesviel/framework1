from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsManager
from .models import Project, Stage
from .serializers import ProjectSerializer, StageSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return Project.objects.all()
        return Project.objects.filter(members=user)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsManager()]
        return [p() if isinstance(p, type) else p for p in self.permission_classes]

    @action(detail=True, methods=["get"])
    def stages(self, request, pk=None):
        project = self.get_object()
        data = StageSerializer(project.stages.all(), many=True).data
        return Response(data)

class StageViewSet(viewsets.ModelViewSet):
    serializer_class = StageSerializer
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        return Stage.objects.all()