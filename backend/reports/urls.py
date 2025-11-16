from django.urls import path
from .views import SummaryView, ByProjectView, ByEngineerView, ExportView

urlpatterns = [
    path("summary/", SummaryView.as_view()),
    path("by_project/", ByProjectView.as_view()),
    path("by_engineer/", ByEngineerView.as_view()),
    path("export/", ExportView.as_view()),
]