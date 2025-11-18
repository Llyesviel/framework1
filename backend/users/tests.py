import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient

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

@pytest.mark.django_db
def test_web_users_list_requires_manager():
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    client = Client()
    client.login(username="e", password="x")
    resp = client.get("/users/")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_web_users_list_manager_ok():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    client = Client()
    client.login(username="m", password="x")
    resp = client.get("/users/")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_api_login_returns_tokens():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    client = APIClient()
    resp = client.post("/api/auth/login/", {"username": "m", "password": "x"}, format="json")
    assert resp.status_code == 200
    assert "access" in resp.data
    assert "refresh" in resp.data

@pytest.mark.django_db
def test_api_users_list_engineer_forbidden():
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    client = APIClient()
    client.force_authenticate(user=e)
    resp = client.get("/api/users/")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_api_users_list_manager_ok():
    m = User.objects.create_user(username="m", email="m@example.com", password="x", role="manager")
    client = APIClient()
    client.force_authenticate(user=m)
    resp = client.get("/api/users/")
    assert resp.status_code == 200

@pytest.mark.django_db
def test_api_user_create_by_engineer_allowed():
    e = User.objects.create_user(username="e", email="e@example.com", password="x", role="engineer")
    client = APIClient()
    client.force_authenticate(user=e)
    payload = {"username": "newuser", "email": "new@example.com", "role": "observer", "password": "p"}
    resp = client.post("/api/users/", payload, format="json")
    assert resp.status_code == 201