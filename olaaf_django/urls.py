from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('authenticate/', TemplateView.as_view(template_name='olaaf_django/index.html'), name='home'),
    path('authenticate', views.authenticate, name='authenticate'),
    path('check-hashes', views.check_hashes, name='check-hashes'),
]
