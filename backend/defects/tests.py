import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage
from defects.models import Defect
from defects.services import change_status

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