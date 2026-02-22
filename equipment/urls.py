from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.EquipmentPostListCreateView.as_view(), name='equipment-posts'),
    path('risk-tips/', views.RiskTipsView.as_view(), name='equipment-risk-tips'),
]