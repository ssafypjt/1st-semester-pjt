from django.urls import path
from . import views

urlpatterns = [
    # 카드 템플릿 목록
    path('templates/', views.list_templates, name='card-templates'),
    # 내 전체 공유 카드 목록 (카드함)
    path('my/', views.my_share_cards, name='share-card-my'),
    # 공유 카드 단건 조회 (공유 링크용)
    path('card/<int:card_id>/', views.share_card_detail, name='share-card-detail'),
    # 공유 카드 삭제
    path('card/<int:card_id>/delete/', views.delete_share_card, name='share-card-delete'),
    # 특정 기록의 공유 카드 목록
    path('<int:record_id>/', views.list_share_cards, name='share-card-list'),
    # 공유 카드 생성 (AI)
    path('<int:record_id>/generate/', views.generate_share_card, name='share-card-generate'),
]
