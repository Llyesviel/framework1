import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage
from defects.models import Defect
from defects.services import change_status
from django.test import Client
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
def test_status_machine_valid_transition():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D")
    change_status(d, Defect.STATUS_IN_PROGRESS, m)
    assert d.status == Defect.STATUS_IN_PROGRESS

@pytest.mark.django_db
def test_engineer_only_self_defect_status_change():
    e1 = User.objects.create_user(username="e1", email="e1@example.com", password="x", role="engineer")
    e2 = User.objects.create_user(username="e2", email="e2@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P")
    p.members.add(e1)
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D", status=Defect.STATUS_IN_PROGRESS, performer=e1)
    with pytest.raises(PermissionError):
        change_status(d, Defect.STATUS_REVIEW, e2)

@pytest.mark.django_db
def test_observer_cannot_be_performer():
    o = User.objects.create_user(username="o", email="o@example.com", password="x", role="observer")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    with pytest.raises(ValueError):
        Defect.objects.create(project=p, stage=s, title="D", performer=o)

@pytest.mark.django_db
def test_integration_create_assign_change_status():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P")
    p.members.add(e)
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D", performer=e)
    change_status(d, Defect.STATUS_IN_PROGRESS, m)
    change_status(d, Defect.STATUS_REVIEW, e)
    assert d.status == Defect.STATUS_REVIEW

@pytest.mark.django_db
def test_filter_defects_by_status():
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    Defect.objects.create(project=p, stage=s, title="D1", status=Defect.STATUS_NEW)
    Defect.objects.create(project=p, stage=s, title="D2", status=Defect.STATUS_CANCELLED)
    assert Defect.objects.filter(status=Defect.STATUS_NEW).count() == 1

@pytest.mark.django_db
def test_web_engineer_cannot_edit_defect():
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P")
    p.members.add(e)
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D")
    client = Client()
    client.login(username="e", password="x")
    resp = client.get(f"/defects/{d.id}/edit/")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_web_manager_can_edit_defect():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D")
    client = Client()
    client.login(username="m", password="x")
    resp = client.get(f"/defects/{d.id}/edit/")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_web_defect_assign_invalid_username_error():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D")
    client = Client()
    client.login(username="m", password="x")
    resp = client.post(f"/defects/{d.id}/assign/", {"username": "unknown"})
    assert resp.status_code == 200
    assert "username" in resp.context.get("form").errors

@pytest.mark.django_db
def test_api_defects_list_manager_ok():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    Defect.objects.create(project=p, stage=s, title="D1")
    client = APIClient()
    client.force_authenticate(user=m)
    resp = client.get("/api/defects/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert len(resp.data) == 1

@pytest.mark.django_db
def test_api_change_status_invalid_transition_400():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D")
    client = APIClient()
    client.force_authenticate(user=m)
    resp = client.post(f"/api/defects/{d.id}/change_status/", {"status": Defect.STATUS_CLOSED}, format="json")
    assert resp.status_code == 400
    assert "Недопустимый переход статуса" in resp.data.get("detail", "")

@pytest.mark.django_db
def test_api_comments_post_requires_text_400():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D")
    client = APIClient()
    client.force_authenticate(user=m)
    resp = client.post(f"/api/defects/{d.id}/comments/", {}, format="json")
    assert resp.status_code == 400
    assert resp.data.get("detail") == "text required"