# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    path('apply-creator/', views.ApplyCreatorView.as_view(), name='apply-creator'),
    path('can-apply-creator/', views.CanApplyCreatorView.as_view(), name='can-apply-creator'),
]