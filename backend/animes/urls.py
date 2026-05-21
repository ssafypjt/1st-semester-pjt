from rest_framework.routers import DefaultRouter
from .views import AnimeViewSet

router = DefaultRouter()
router.register('', AnimeViewSet, basename='anime')

urlpatterns = router.urls
