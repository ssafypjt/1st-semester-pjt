from django.urls import path
from . import views

urlpatterns = [
    # 카드 템플릿 목록
    path('templates/', views.list_templates, name='card-templates'),
    # 공유 카드 단건 조회 (공유 링크용)
    path('card/<int:card_id>/', views.share_card_detail, name='share-card-detail'),
    # 특정 기록의 공유 카드 목록
    path('<int:record_id>/', views.list_share_cards, name='share-card-list'),
    # 공유 카드 생성 (AI)
    path('<int:record_id>/generate/', views.generate_share_card, name='share-card-generate'),
]
