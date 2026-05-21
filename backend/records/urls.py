from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import RecordViewSet, protected_media, upload_image

router = DefaultRouter()
router.register('', RecordViewSet, basename='record')

urlpatterns = [
    # 다꾸용 이미지 업로드
    path('upload/', upload_image, name='upload-image'),
    # 업로드된 이미지의 보호된 미디어 응답 (uploader 본인만 200)
    path('uploads/<int:pk>/', protected_media, name='protected-media'),
] + router.urls
