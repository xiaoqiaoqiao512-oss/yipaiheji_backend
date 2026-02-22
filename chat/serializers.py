from rest_framework import serializers
from .models import Message
from users.models import User


class MessageSerializer(serializers.ModelSerializer):
    """消息序列化器（支持私聊和群聊）"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.avatar', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True, allow_null=True)

    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_username', 'sender_avatar',
            'receiver', 'receiver_username',
            'message_type', 'groupbuy',
            'content', 'is_read', 'created_at', 'updated_at'
        ]
        read_only_fields = ['sender', 'sender_username', 'sender_avatar', 'created_at', 'updated_at']

    def create(self, validated_data):
        """创建消息时自动关联发送者"""
        user = self.context['request'].user
        validated_data['sender'] = user
        
        # 如果是私聊，必须指定 receiver
        if validated_data.get('message_type') == 'private' and not validated_data.get('receiver'):
            raise serializers.ValidationError({"receiver": "私聊必须指定接收者"})
        
        # 如果是群聊，必须指定 groupbuy
        if validated_data.get('message_type') == 'groupbuy' and not validated_data.get('groupbuy'):
            raise serializers.ValidationError({"groupbuy": "群聊必须指定拼单"})
        
        return super().create(validated_data)


class MessageListSerializer(serializers.ModelSerializer):
    """消息列表序列化器（简化版）"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.avatar', read_only=True)
    created_at = serializers.DateTimeField(format="%m-%d %H:%M", read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'sender_username', 'sender_avatar',
            'message_type', 'content', 'is_read', 'created_at'
        ]