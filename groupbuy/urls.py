from django.urls import path
from . import views

urlpatterns = [
    # 拼单列表 + 发布
    path('', views.GroupBuyListCreateView.as_view(), name='groupbuy-list'),
    
    # 拼单详情 + 修改
    path('<int:pk>/', views.GroupBuyDetailView.as_view(), name='groupbuy-detail'),
    
    # 加入拼单
    path('<int:pk>/join/', views.JoinGroupBuyView.as_view(), name='join-groupbuy'),
    
    # 退出拼单
    path('<int:pk>/leave/', views.LeaveGroupBuyView.as_view(), name='leave-groupbuy'),
]