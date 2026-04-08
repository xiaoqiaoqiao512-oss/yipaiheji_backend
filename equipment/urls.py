from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.EquipmentPostListCreateView.as_view(), name='equipment-posts'),
    path('posts/<int:pk>/', views.EquipmentPostDetailView.as_view(), name='equipment-post-detail'),
    path('posts/<int:pk>/contact/', views.ContactPublisherView.as_view(), name='equipment-contact-publisher'),
    path('risk-tips/', views.RiskTipsView.as_view(), name='equipment-risk-tips'),
]