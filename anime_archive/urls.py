from django.urls import path

from .views import (
    analyze_api,
    create_record_api,
    diary_detail_page,
    diary_list_page,
    home,
    login_page,
    mypage,
    records_api,
    review_detail_page,
    review_list_page,
    share_page,
    signup_page,
)


urlpatterns = [
    path("", login_page, name="home"),
    path("deokkku/", home, name="deokkku_home"),
    path("deokkku/home/", home, name="deokkku_home_page"),
    path("deokkku/login/", login_page, name="deokkku_login"),
    path("deokkku/join/", signup_page, name="deokkku_join"),
    path("login/", login_page, name="login"),
    path("signup/", signup_page, name="signup"),
    path("deokkku/my_album/", diary_list_page, name="diary_list"),
    path("diaries/<int:diary_id>/", diary_detail_page, name="diary_detail"),
    path("reviews/", review_list_page, name="review_list"),
    path("reviews/<int:review_id>/", review_detail_page, name="review_detail"),
    path("mypage/", mypage, name="mypage"),
    path("share/<int:diary_id>/", share_page, name="share"),
    path("api/records/", records_api, name="records_api"),
    path("api/analyze/", analyze_api, name="analyze_api"),
    path("api/records/create/", create_record_api, name="create_record_api"),
]
