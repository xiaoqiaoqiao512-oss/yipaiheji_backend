# demands/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 需求列表和创建
    path('', views.DemandListCreateView.as_view(), name='demand-list'),
    
    # 需求详情、更新、删除
    path('<int:pk>/', views.DemandDetailView.as_view(), name='demand-detail'),
    
    # 需求评论
    path('<int:demand_id>/comments/', views.DemandCommentListView.as_view(), name='demand-comments'),
    path('comments/create/', views.DemandCommentCreateView.as_view(), name='comment-create'),
    path('comments/<int:comment_id>/accept/', views.AcceptCommentView.as_view(), name='accept-comment'),
    
    # 我的需求和报价
    path('my-demands/', views.MyDemandsView.as_view(), name='my-demands'),
    path('my-bids/', views.MyBidsView.as_view(), name='my-bids'),

    #tag
    path('<int:demand_id>/recommended_creators/', views.DemandRecommendedCreatorsView.as_view(), name='demand-recommended-creators'),

    #单图上传
    path('upload-image/', views.SingleImageUploadView.as_view(), name='upload-image'),
]