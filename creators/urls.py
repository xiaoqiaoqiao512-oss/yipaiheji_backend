# creators/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 创作者档案
    path('profile/', views.CreatorProfileView.as_view(), name='creator-profile'),
    path('public/<int:id>/', views.CreatorPublicView.as_view(), name='creator-public'),
    
    # 作品管理
    path('works/', views.WorkListCreateView.as_view(), name='work-list'),
    path('works/<int:pk>/', views.WorkDetailView.as_view(), name='work-detail'),
    # 添加作品排序
    path('works/reorder/', views.ReorderWorksView.as_view(), name='work-reorder'),
    path('works/<int:pk>/order/', views.UpdateWorkOrderView.as_view(), name='work-order'),
    
    # 服务项目管理
    path('services/', views.ServiceListCreateView.as_view(), name='service-list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),
    
    # 公开作品墙
    path('public-works/', views.PublicWorksView.as_view(), name='public-works'),
]