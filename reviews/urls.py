from django.urls import path

from .views import create_review

urlpatterns = [
    path('product/<slug:slug>/review/', create_review, name='create_review'),
]
