from django.db.models import Count
from defects.models import Defect

def summary():
    return {
        "total": Defect.objects.count(),
        "by_status": list(
            Defect.objects.values("status").annotate(count=Count("id")).order_by("status")
        ),
        "by_priority": list(
            Defect.objects.values("priority").annotate(count=Count("id")).order_by("priority")
        ),
    }

def by_project(project_id: int):
    qs = Defect.objects.filter(project_id=project_id)
    return {
        "project_id": project_id,
        "total": qs.count(),
        "by_status": list(qs.values("status").annotate(count=Count("id"))),
    }

def by_engineer(user_id: int):
    qs = Defect.objects.filter(performer_id=user_id)
    return {
        "engineer_id": user_id,
        "total": qs.count(),
        "by_status": list(qs.values("status").annotate(count=Count("id"))),
    }