import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage
from defects.models import Defect
from reports.analytics import summary, by_project, by_engineer
from django.test import Client
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
def test_summary_counts():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    Defect.objects.create(project=p, stage=s, title="D1")
    Defect.objects.create(project=p, stage=s, title="D2")
    data = summary()
    assert data["total"] == 2

@pytest.mark.django_db
def test_by_project():
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    Defect.objects.create(project=p, stage=s, title="D1")
    data = by_project(p.id)
    assert data["project_id"] == p.id

@pytest.mark.django_db
def test_web_reports_export_csv_manager_ok():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    client = Client()
    client.login(username="m", password="x")
    resp = client.get("/reports/export/?download=csv")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8")
    assert "id,project,stage,title,status,priority,performer,deadline" in text.replace(";", ",")

@pytest.mark.django_db
def test_api_reports_export_permission():
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    client = APIClient()
    client.force_authenticate(user=e)
    resp_forbidden = client.get("/api/reports/export/")
    client.force_authenticate(user=m)
    resp_ok = client.get("/api/reports/export/")
    assert resp_forbidden.status_code == 403
    assert resp_ok.status_code == 200