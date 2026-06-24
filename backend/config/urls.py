"""Deokkku (덕꾸) URL configuration."""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView
from django.views.generic import TemplateView


class FrontendAppView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.request.path
        page = 'home'
        object_id = None

        if path in ('/', '/deokkku/login/', '/login/'):
            page = 'login'
        elif path in ('/deokkku/join/', '/signup/'):
            page = 'signup'
        elif path in ('/deokkku/', '/deokkku/home/'):
            page = 'home'
        elif path in ('/deokkku/my_album/', '/diaries/'):
            page = 'diary-list'
        elif path.startswith('/diaries/'):
            page = 'diary-detail'
            object_id = self._path_id(path)
        elif path == '/reviews/':
            page = 'review-list'
        elif path.startswith('/reviews/'):
            page = 'review-detail'
            object_id = self._path_id(path)
        elif path == '/mypage/':
            page = 'mypage'
        elif path.startswith('/share/'):
            page = 'share'
            object_id = self._path_id(path)

        context['initial_route'] = {
            'page': page,
            'objectId': object_id,
        }
        return context

    @staticmethod
    def _path_id(path):
        parts = [part for part in path.strip('/').split('/') if part]
        if not parts:
            return None
        try:
            return int(parts[-1])
        except ValueError:
            return None


class DistFrontendAppView(TemplateView):
    def get(self, request, *args, **kwargs):
        index_path = settings.FRONTEND_DIR / 'dist' / 'index.html'
        if index_path.exists():
            return HttpResponse(
                index_path.read_text(encoding='utf-8'),
                content_type='text/html; charset=utf-8',
            )
        return FrontendAppView.as_view()(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/works/', include('works.urls')),

    path('api/albums/', include('albums.urls')),
    path('api/records/', include('records.urls')),
    path('api/shares/', include('shares.urls')),
    path('', RedirectView.as_view(url='/deokkku/login/', permanent=False), name='home'),
    path('login/', FrontendAppView.as_view(), name='login-page'),
    path('signup/', FrontendAppView.as_view(), name='signup-page'),
    path('deokkku/login/', FrontendAppView.as_view(), name='deokkku-login-page'),
    path('deokkku/join/', FrontendAppView.as_view(), name='deokkku-join-page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Vue SPA fallback
urlpatterns += [
    re_path(r'^(?!api/|admin/|static/|media/).*$',
            DistFrontendAppView.as_view(),
            name='spa'),
]
