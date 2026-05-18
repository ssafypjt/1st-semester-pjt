from django.urls import path

from .views import analyze_api, create_record_api, home, records_api


urlpatterns = [
    path("", home, name="home"),
    path("api/records/", records_api, name="records_api"),
    path("api/analyze/", analyze_api, name="analyze_api"),
    path("api/records/create/", create_record_api, name="create_record_api"),
]
