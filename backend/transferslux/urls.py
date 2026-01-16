from api import views
from api.sitemaps import CompleteSitemap
from django.conf import settings
from django.conf.urls import handler404
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

handler404 = 'api.views.page_not_found'
handler500 = 'api.views.internal_server_error'

sitemaps = {
    'pages': CompleteSitemap,
}

urlpatterns = [
    path('dj-admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Основные URL-паттерны вашего приложения
urlpatterns += i18n_patterns(
    path('', include(('api.urls', 'api'), namespace='api')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]