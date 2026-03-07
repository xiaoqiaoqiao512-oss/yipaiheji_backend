# creators/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建 router 并注册视图集（用于作品图片管理）
router = DefaultRouter()
router.register(r'work-images', views.WorkImageViewSet, basename='workimage')

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

    #tag
    path('tags/', views.TagListView.as_view(), name='tag-list'),

    # 地图相关
    path('map/locations/', views.LocationMapView.as_view(), name='location-map'),
    path('map/my-locations/', views.MyLocationMapView.as_view(), name='my-location-map'),
    path('map/locations/<int:location_id>/works/', views.LocationWorksView.as_view(), name='location-works'),

    # 点赞
    path('works/<int:work_id>/like/', views.WorkLikeToggleView.as_view(), name='work-like'),
    
    # 评论
    path('works/<int:work_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('comments/<int:pk>/', views.CommentDetailView.as_view(), name='comment-detail'),
    
    # 收藏
    path('works/<int:work_id>/favorite/', views.FavoriteToggleView.as_view(), name='favorite-toggle'),
    path('favorites/', views.UserFavoriteListView.as_view(), name='user-favorites'),
]

# 添加 router 生成的 URL（作品图片管理接口）
urlpatterns += router.urls