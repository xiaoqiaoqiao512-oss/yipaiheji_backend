from django.urls import path
from . import views

urlpatterns = [
    # 发送消息（通用接口，支持私聊和群聊）
    path('send/', views.SendMessageView.as_view(), name='send-message'),
    
    # 私聊相关（原来的）
    path('conversation/<int:user_id>/', views.PrivateMessagesView.as_view(), name='get-conversation'),
    path('inbox/', views.InboxView.as_view(), name='inbox'),
    path('sent/', views.SentBoxView.as_view(), name='sent-box'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread-count'),
    path('mark-read/<int:user_id>/', views.MarkMessagesAsReadView.as_view(), name='mark-as-read'),
    
    # 拼单群聊
    path('groupbuy/<int:groupbuy_id>/', views.GroupBuyMessagesView.as_view(), name='groupbuy-messages'),
]