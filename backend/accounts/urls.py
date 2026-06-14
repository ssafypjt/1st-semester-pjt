from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.csrf, name='csrf'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me, name='me'),
    path('me/update/', views.profile_update, name='profile-update'),
    path('password/change/', views.password_change, name='password-change'),
    # 유저 프로필 공개 조회
    path('users/<int:pk>/', views.user_profile, name='user-profile'),
    # 팔로우 토글
    path('users/<int:pk>/follow/', views.follow_toggle, name='follow-toggle'),
    # 팔로워 / 팔로잉 목록
    path('users/<int:pk>/followers/', views.follower_list, name='follower-list'),
    path('users/<int:pk>/following/', views.following_list, name='following-list'),
]
