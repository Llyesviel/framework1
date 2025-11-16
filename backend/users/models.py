from django.contrib.auth.models import AbstractUser, Group
from django.db import models

class User(AbstractUser):
    ROLE_MANAGER = "manager"
    ROLE_ENGINEER = "engineer"
    ROLE_OBSERVER = "observer"
    ROLE_CHOICES = [
        (ROLE_MANAGER, "manager"),
        (ROLE_ENGINEER, "engineer"),
        (ROLE_OBSERVER, "observer"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ENGINEER)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_groups()

    def sync_groups(self):
        groups = {
            self.ROLE_MANAGER: Group.objects.get_or_create(name="manager")[0],
            self.ROLE_ENGINEER: Group.objects.get_or_create(name="engineer")[0],
            self.ROLE_OBSERVER: Group.objects.get_or_create(name="observer")[0],
        }
        for g in Group.objects.filter(user=self):
            g.user_set.remove(self)
        groups[self.role].user_set.add(self)

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    @property
    def is_engineer(self):
        return self.role == self.ROLE_ENGINEER

    @property
    def is_observer(self):
        return self.role == self.ROLE_OBSERVER