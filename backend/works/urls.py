from rest_framework.routers import DefaultRouter
from .views import WorkViewSet

router = DefaultRouter()
router.register('', WorkViewSet, basename='work')

urlpatterns = router.urls
