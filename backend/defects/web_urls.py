from django.urls import path
from .web_views import (
    DefectListView,
    DefectDetailView,
    DefectCreateView,
    DefectUpdateView,
    DefectStatusUpdateView,
    AttachmentUploadView,
    DefectAssignView,
    DefectDeleteView,
    DefectsExportCSVView,
    DefectsExportExcelView,
    DefectExportCSVView,
    DefectExportExcelView,
    DefectAcceptView,
    DefectSubmitReportView,
)

urlpatterns = [
    path("", DefectListView.as_view(), name="defects_list"),
    path("create/", DefectCreateView.as_view(), name="defect_create"),
    path("<int:pk>/", DefectDetailView.as_view(), name="defect_detail"),
    path("<int:pk>/edit/", DefectUpdateView.as_view(), name="defect_edit"),
    path("<int:pk>/change_status/", DefectStatusUpdateView.as_view(), name="defect_change_status"),
    path("<int:pk>/attachments/", AttachmentUploadView.as_view(), name="defect_upload_attachments"),
    path("<int:pk>/assign/", DefectAssignView.as_view(), name="defect_assign"),
    path("<int:pk>/accept/", DefectAcceptView.as_view(), name="defect_accept"),
    path("<int:pk>/submit_report/", DefectSubmitReportView.as_view(), name="defect_submit_report"),
    path("<int:pk>/delete/", DefectDeleteView.as_view(), name="defect_delete"),
    path("export/csv/", DefectsExportCSVView.as_view(), name="defects_export_csv"),
    path("export/xls/", DefectsExportExcelView.as_view(), name="defects_export_xls"),
    path("<int:pk>/export/csv/", DefectExportCSVView.as_view(), name="defect_export_csv"),
    path("<int:pk>/export/xls/", DefectExportExcelView.as_view(), name="defect_export_xls"),
]