import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage
from django.test import Client

User = get_user_model()

@pytest.mark.django_db
def test_project_stage_creation():
    u = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    p.members.add(u)
    s = Stage.objects.create(project=p, title="S")
    assert s.project_id == p.id

@pytest.mark.django_db
def test_web_projects_export_csv_bom_and_delimiter():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    Project.objects.create(title="P1")
    client = Client()
    client.login(username="m", password="x")
    resp = client.get("/projects/export/projects/csv/")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8")
    assert text.startswith("\ufeff")
    assert ";" in text

@pytest.mark.django_db
@pytest.mark.integration
def test_integration_projects_export_filters_by_engineer_membership():
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    p1 = Project.objects.create(title="P1")
    p2 = Project.objects.create(title="P2")
    p1.members.add(e)
    client = Client(); client.login(username="e", password="x")
    resp = client.get("/projects/export/projects/csv/")
    assert resp.status_code == 200
    text = resp.content.decode("utf-8")
    assert "P1" in text
    assert "P2" not in text