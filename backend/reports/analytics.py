from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from defects.models import Defect
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from projects.models import Project

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

def by_day(days: int = 30):
    """Return daily activity based on Defect additions per priority.
    Uses admin LogEntry ADDITION events to avoid relying on missing created_at.
    """
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    ct = ContentType.objects.get_for_model(Defect)
    # Gather additions grouped by day
    additions = (
        LogEntry.objects.filter(
            content_type_id=ct.id,
            action_flag=ADDITION,
            action_time__date__gte=start,
            action_time__date__lte=end,
        )
        .annotate(day=TruncDate("action_time"))
        .values("day")
        .annotate(ids=Count("object_id"))
    )
    # Build date index
    dates = [start + timedelta(days=i) for i in range(days)]
    labels = [d.strftime("%d.%m") for d in dates]
    series = {"low": [0]*days, "medium": [0]*days, "high": [0]*days}
    idx_map = {dates[i]: i for i in range(days)}
    # For each day, fetch priorities of created defects
    daily_ids = (
        LogEntry.objects.filter(
            content_type_id=ct.id,
            action_flag=ADDITION,
            action_time__date__gte=start,
            action_time__date__lte=end,
        )
        .annotate(day=TruncDate("action_time"))
        .values_list("day", "object_id")
    )
    day_to_ids = {}
    for day, oid in daily_ids:
        dd = day.date() if hasattr(day, "date") else day
        day_to_ids.setdefault(dd, []).append(oid)
    for dd, ids in day_to_ids.items():
        i = idx_map.get(dd)
        if i is None:
            continue
        prios = Defect.objects.filter(id__in=ids).values_list("priority", flat=True)
        # Count per priority for this day
        low = sum(1 for p in prios if p == "low")
        med = sum(1 for p in prios if p == "medium")
        high = sum(1 for p in prios if p == "high")
        series["low"][i] = low
        series["medium"][i] = med
        series["high"][i] = high
    return {"labels": labels, "series": series}

def by_day_projects(days: int = 7):
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    ct = ContentType.objects.get_for_model(Project)
    rows = (
        LogEntry.objects.filter(
            content_type_id=ct.id,
            action_flag=ADDITION,
            action_time__date__gte=start,
            action_time__date__lte=end,
        )
        .annotate(day=TruncDate("action_time"))
        .values("day")
        .annotate(count=Count("id"))
    )
    dates = [start + timedelta(days=i) for i in range(days)]
    labels = [d.strftime("%d.%m") for d in dates]
    counts = [0]*days
    idx_map = {dates[i]: i for i in range(days)}
    for r in rows:
        dd = r["day"].date() if hasattr(r["day"], "date") else r["day"]
        i = idx_map.get(dd)
        if i is not None:
            counts[i] = r["count"]
    return {"labels": labels, "counts": counts}

def by_day_defects(days: int = 7):
    end = timezone.localdate()
    start = end - timedelta(days=days - 1)
    ct = ContentType.objects.get_for_model(Defect)
    rows = (
        LogEntry.objects.filter(
            content_type_id=ct.id,
            action_flag=ADDITION,
            action_time__date__gte=start,
            action_time__date__lte=end,
        )
        .annotate(day=TruncDate("action_time"))
        .values("day")
        .annotate(count=Count("id"))
    )
    dates = [start + timedelta(days=i) for i in range(days)]
    labels = [d.strftime("%d.%m") for d in dates]
    counts = [0]*days
    idx_map = {dates[i]: i for i in range(days)}
    for r in rows:
        dd = r["day"].date() if hasattr(r["day"], "date") else r["day"]
        i = idx_map.get(dd)
        if i is not None:
            counts[i] = r["count"]
    return {"labels": labels, "counts": counts}