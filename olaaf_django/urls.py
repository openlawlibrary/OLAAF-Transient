from django.urls import path

from . import views

urlpatterns = [
    path('authenticate', views.authenticate, name='authenticate'),
    path('check-hashes', views.check_hashes, name='check-hashes'),
]
