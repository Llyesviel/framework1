from django.db import models
from django.conf import settings

class Project(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "активен"),
        (STATUS_CLOSED, "закрыт"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="projects", blank=True)

    def __str__(self):
        return self.title

class Stage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="stages")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project_id}:{self.title}"

class BuildObject(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="build_objects")
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project_id}:{self.title}"