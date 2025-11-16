from rest_framework.routers import DefaultRouter
from .views import DefectViewSet

router = DefaultRouter()
router.register(r"", DefectViewSet, basename="defect")

urlpatterns = router.urls