from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsManager
from .analytics import summary, by_project, by_engineer
import csv
from django.http import HttpResponse

class SummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = summary()
        return Response(data)

class ByProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get("project_id")
        return Response(by_project(int(project_id)))

class ByEngineerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        engineer_id = request.query_params.get("engineer_id")
        return Response(by_engineer(int(engineer_id)))

class ExportView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        from defects.models import Defect
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=defects.csv"
        writer = csv.writer(response)
        writer.writerow(["id", "project", "stage", "title", "status", "priority", "performer", "deadline"])
        for d in Defect.objects.all().select_related("project", "stage", "performer"):
            writer.writerow([
                d.id,
                d.project_id,
                d.stage_id or "",
                d.title,
                d.status,
                d.priority,
                d.performer_id or "",
                d.deadline or "",
            ])
        return response