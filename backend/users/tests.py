import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_manager_role_group_sync():
    u = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    assert u.is_manager

@pytest.mark.django_db
def test_engineer_role_group_sync():
    u = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    assert u.is_engineer

@pytest.mark.django_db
def test_observer_role_group_sync():
    u = User.objects.create_user(username="o", email="o@example.com", password="x", role="observer")
    assert u.is_observer