from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView
from django.urls import path

from .views import account_view, login_view, logout_view, profile_view, register_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('password-change/', PasswordChangeView.as_view(template_name='password_change.html'), name='password_change'),
    path('password-change/done/', PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('account/', account_view, name='account'),
    path('account/profile/', profile_view, name='profile'),
]
