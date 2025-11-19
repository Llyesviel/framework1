import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage
from defects.models import Defect
from defects.services import change_status
from django.test import Client
from rest_framework.test import APIClient
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

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
@pytest.mark.integration
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
def test_xss_comment_escaped_in_detail_page():
    e = User.objects.create_user(username="e2", email="e2@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P2")
    s = Stage.objects.create(project=p, title="S2")
    d = Defect.objects.create(project=p, stage=s, title="T", performer=e, status=Defect.STATUS_IN_PROGRESS)
    c = Client(); c.login(username="e2", password="x")
    c.post(f"/defects/{d.id}/submit_report/", {"text": "<script>alert(1)</script>"})
    resp = c.get(f"/defects/{d.id}/")
    html = resp.content.decode("utf-8")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

@pytest.mark.django_db
def test_csrf_required_on_submit_report():
    e = User.objects.create_user(username="e3", email="e3@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P3")
    s = Stage.objects.create(project=p, title="S3")
    d = Defect.objects.create(project=p, stage=s, title="T3", performer=e)
    c = Client(enforce_csrf_checks=True); c.login(username="e3", password="x")
    r1 = c.post(f"/defects/{d.id}/submit_report/", {"text": "t"})
    assert r1.status_code == 403
    g = c.get(f"/defects/{d.id}/")
    csrftoken = c.cookies.get("csrftoken").value
    r2 = c.post(f"/defects/{d.id}/submit_report/", {"text": "t", "csrfmiddlewaretoken": csrftoken}, HTTP_REFERER=f"/defects/{d.id}/")
    assert r2.status_code in (302, 200)

@pytest.mark.django_db
def test_sql_injection_attempt_in_search_param_no_error():
    e = User.objects.create_user(username="e4", email="e4@example.com", password="x", role="engineer")
    p1 = Project.objects.create(title="P4")
    p2 = Project.objects.create(title="PX")
    s1 = Stage.objects.create(project=p1, title="S4")
    s2 = Stage.objects.create(project=p2, title="SX")
    d1 = Defect.objects.create(project=p1, stage=s1, title="A", performer=e)
    d2 = Defect.objects.create(project=p2, stage=s2, title="Z")
    c = Client(); c.login(username="e4", password="x")
    resp = c.get("/defects/", {"q": "' OR 1=1 --"})
    assert resp.status_code == 200
    html = resp.content.decode("utf-8")
    assert "Z" not in html

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

@pytest.mark.django_db
@pytest.mark.integration
def test_integration_web_full_flow_manager_engineer_close():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P")
    p.members.add(e)
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D", performer=e)
    c = Client()
    c.login(username="e", password="x")
    r1 = c.post(f"/defects/{d.id}/accept/")
    assert r1.status_code in (302, 200)
    c.logout()
    c.login(username="e", password="x")
    r2 = c.post(f"/defects/{d.id}/submit_report/", {"text": "work done"})
    assert r2.status_code in (302, 200)
    c.logout()
    c.login(username="m", password="x")
    r3 = c.post(f"/defects/{d.id}/change_status/", {"status": Defect.STATUS_CLOSED})
    assert r3.status_code in (302, 200)
    d.refresh_from_db()
    assert d.status == Defect.STATUS_CLOSED
    assert d.comments.count() == 1

@pytest.mark.django_db
@pytest.mark.integration
def test_integration_api_flow_create_assign_and_transition():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P")
    p.members.add(e)
    s = Stage.objects.create(project=p, title="S")
    client_m = APIClient(); client_m.force_authenticate(user=m)
    resp_create = client_m.post("/api/defects/", {"project": p.id, "stage": s.id, "title": "D", "performer": e.id}, format="json")
    assert resp_create.status_code == 201
    defect_id = resp_create.data["id"]
    client_e = APIClient(); client_e.force_authenticate(user=e)
    r1 = client_e.post(f"/api/defects/{defect_id}/change_status/", {"status": Defect.STATUS_IN_PROGRESS}, format="json")
    assert r1.status_code == 200
    r2 = client_e.post(f"/api/defects/{defect_id}/comments/", {"text": "report"}, format="json")
    assert r2.status_code == 201
    r3 = client_e.post(f"/api/defects/{defect_id}/change_status/", {"status": Defect.STATUS_REVIEW}, format="json")
    assert r3.status_code == 200
    r4 = client_m.post(f"/api/defects/{defect_id}/change_status/", {"status": Defect.STATUS_CLOSED}, format="json")
    assert r4.status_code == 200
    d = Defect.objects.get(pk=defect_id)
    assert d.status == Defect.STATUS_CLOSED

@pytest.mark.django_db
@pytest.mark.integration
def test_integration_api_attachments_upload():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    p = Project.objects.create(title="P")
    p.members.add(e)
    s = Stage.objects.create(project=p, title="S")
    d = Defect.objects.create(project=p, stage=s, title="D", performer=e)
    client_e = APIClient(); client_e.force_authenticate(user=e)
    file = SimpleUploadedFile("photo.jpg", b"data", content_type="image/jpeg")
    resp = client_e.post(f"/api/defects/{d.id}/attachments/", {"file": file}, format="multipart")
    assert resp.status_code == 201
    d.refresh_from_db()
    assert d.attachments.count() == 1

@pytest.mark.django_db
def test_api_sql_injection_attempt_no_error_and_no_bypass():
    e = User.objects.create_user(username="e5", email="e5@example.com", password="x", role="engineer")
    m = User.objects.create_user(username="m5", email="m5@example.com", password="x", role="manager")
    p1 = Project.objects.create(title="P5")
    p2 = Project.objects.create(title="P6")
    p1.members.add(e)
    s1 = Stage.objects.create(project=p1, title="S5")
    s2 = Stage.objects.create(project=p2, title="S6")
    Defect.objects.create(project=p1, stage=s1, title="A1")
    Defect.objects.create(project=p2, stage=s2, title="B1")
    client_e = APIClient(); client_e.force_authenticate(user=e)
    r = client_e.get("/api/defects/", {"project": "1 OR 1=1"})
    assert r.status_code in (200, 400)
    data = r.json()
    titles = [d["title"] for d in data] if isinstance(data, list) else [item.get("title") for item in data.get("results", [])]
    assert "B1" not in titles