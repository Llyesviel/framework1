import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage
from defects.models import Defect
from reports.analytics import summary, by_project, by_engineer

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