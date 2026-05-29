"""Deokkku (덕꾸) URL configuration."""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/works/', include('works.urls')),
    path('api/albums/', include('albums.urls')),
    path('api/records/', include('records.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Vue SPA fallback
urlpatterns += [
    re_path(r'^(?!api/|admin/|static/|media/).*$',
            TemplateView.as_view(template_name='index.html'),
            name='spa'),
]
