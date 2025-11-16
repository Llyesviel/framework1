from django.urls import path
from .web_views import (
    DefectListView,
    DefectDetailView,
    DefectCreateView,
    DefectUpdateView,
    DefectStatusUpdateView,
    AttachmentUploadView,
)

urlpatterns = [
    path("", DefectListView.as_view(), name="defects_list"),
    path("create/", DefectCreateView.as_view(), name="defect_create"),
    path("<int:pk>/", DefectDetailView.as_view(), name="defect_detail"),
    path("<int:pk>/edit/", DefectUpdateView.as_view(), name="defect_edit"),
    path("<int:pk>/change_status/", DefectStatusUpdateView.as_view(), name="defect_change_status"),
    path("<int:pk>/attachments/", AttachmentUploadView.as_view(), name="defect_upload_attachments"),
]