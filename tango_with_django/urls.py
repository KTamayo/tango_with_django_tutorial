from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rango/', include('rango.urls')), 
    (r'^accounts/', include('registration.backends.simple.urls')),
)

if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += patterns(
            'django.views.static',
            (r'^media/(?P<path>.*)',
            'serve',
            {'document_root':settings.MEDIA_ROOT}), )
