from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import Message
from .serializers import MessageSerializer, MessageListSerializer
from groupbuy.models import GroupBuy


class SendMessageView(generics.CreateAPIView):
    """发送消息（支持私聊和群聊）"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        """发送消息前检查权限"""
        message_type = self.request.data.get('message_type', 'private')
        
        # 群聊：检查用户是否在拼单里
        if message_type == 'groupbuy':
            groupbuy_id = self.request.data.get('groupbuy')
            groupbuy = GroupBuy.objects.get(id=groupbuy_id)
            
            is_member = (
                groupbuy.initiator == self.request.user or
                groupbuy.members.filter(user=self.request.user).exists()
            )
            
            if not is_member:
                raise permissions.exceptions.PermissionDenied("只有拼单成员可以聊天")
        
        serializer.save(sender=self.request.user)


class GroupBuyMessagesView(generics.ListCreateAPIView):
    """拼单群聊消息"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageListSerializer

    def get_queryset(self):
        """只返回指定拼单的群聊消息"""
        groupbuy_id = self.kwargs.get('groupbuy_id')
        return Message.objects.filter(
            message_type='groupbuy',
            groupbuy_id=groupbuy_id
        ).order_by('created_at')

    def perform_create(self, serializer):
        """创建群聊消息"""
        groupbuy_id = self.kwargs.get('groupbuy_id')
        groupbuy = GroupBuy.objects.get(id=groupbuy_id)

        # 检查用户是否在拼单里
        is_member = (
            groupbuy.initiator == self.request.user or
            groupbuy.members.filter(user=self.request.user).exists()
        )

        if not is_member:
            raise permissions.exceptions.PermissionDenied("只有拼单成员可以聊天")

        serializer.save(
            sender=self.request.user,
            message_type='groupbuy',
            groupbuy=groupbuy
        )


class PrivateMessagesView(generics.ListCreateAPIView):
    """私聊消息（原来的功能）"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageListSerializer

    def get_queryset(self):
        """获取与指定用户的私聊"""
        user = self.request.user
        other_user_id = self.kwargs.get('user_id')

        messages = Message.objects.filter(
            message_type='private'
        ).filter(
            Q(sender=user, receiver_id=other_user_id) |
            Q(sender_id=other_user_id, receiver=user)
        ).order_by('created_at')

        return messages

    def list(self, request, *args, **kwargs):
        """查看消息后自动标记为已读"""
        response = super().list(request, *args, **kwargs)

        other_user_id = self.kwargs.get('user_id')
        Message.objects.filter(
            message_type='private',
            receiver=request.user,
            sender_id=other_user_id,
            is_read=False
        ).update(is_read=True)

        return response

    def perform_create(self, serializer):
        """创建私聊消息"""
        serializer.save(
            sender=self.request.user,
            message_type='private'
        )


class InboxView(generics.ListAPIView):
    """收件箱 - 获取所有接收到的私聊"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageListSerializer

    def get_queryset(self):
        """返回当前用户接收到的所有私聊"""
        return Message.objects.filter(
            message_type='private',
            receiver=self.request.user
        ).order_by('-created_at')


class SentBoxView(generics.ListAPIView):
    """发件箱 - 获取所有发送的私聊"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageListSerializer

    def get_queryset(self):
        """返回当前用户发送的所有私聊"""
        return Message.objects.filter(
            message_type='private',
            sender=self.request.user
        ).order_by('-created_at')


class UnreadCountView(APIView):
    """未读消息计数"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """获取未读私聊消息总数"""
        unread_count = Message.objects.filter(
            message_type='private',
            receiver=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': unread_count})


class MarkMessagesAsReadView(APIView):
    """标记消息为已读"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        """标记与指定用户的所有消息为已读"""
        Message.objects.filter(
            message_type='private',
            receiver=request.user,
            sender_id=user_id,
            is_read=False
        ).update(is_read=True)
        
        return Response({'status': 'messages marked as read'})