from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('news/', include('news.urls')),
    path('forum/', include('forum.urls')),
    path('events/', include('events.urls')),
    path('polls/', include('polls_app.urls')),
    path('announcements/', include('announcements.urls')),
    path('gallery/', include('gallery.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('relax/', include('relax.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
