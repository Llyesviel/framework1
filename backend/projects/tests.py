import pytest
from django.contrib.auth import get_user_model
from projects.models import Project, Stage

User = get_user_model()

@pytest.mark.django_db
def test_project_stage_creation():
    u = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    p = Project.objects.create(title="P")
    p.members.add(u)
    s = Stage.objects.create(project=p, title="S")
    assert s.project_id == p.id