from django.conf.urls import url

from . import views

app_name = 'backend'
urlpatterns = [
    url(r'^query/$', views.query, name='query'),
    url(r'^tips/$', views.tips, name='tips'),
]
