# demands/serializers.py
from rest_framework import serializers
from .models import Demand, DemandComment
from users.models import User

class DemandSerializer(serializers.ModelSerializer):
    """需求序列化器"""
    publisher_username = serializers.CharField(source='publisher.username', read_only=True)
    publisher_avatar = serializers.ImageField(source='publisher.avatar', read_only=True)
    
    # 时间格式化
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    shooting_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    
    class Meta:
        model = Demand
        fields = [
            'id', 'publisher', 'publisher_username', 'publisher_avatar',
            'title', 'demand_type', 'description', 'shooting_time',
            'location', 'campus_location', 'budget', 'min_budget', 'max_budget',
            'people_count', 'status', 'tags', 'special_topic',
            'reference_images', 'view_count', 'comment_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['publisher', 'view_count', 'comment_count', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """创建需求时，自动关联当前登录用户"""
        user = self.context['request'].user
        validated_data['publisher'] = user
        return super().create(validated_data)


class DemandListSerializer(serializers.ModelSerializer):
    """需求列表序列化器（简化版）"""
    publisher_username = serializers.CharField(source='publisher.username', read_only=True)
    created_at = serializers.DateTimeField(format="%m-%d %H:%M", read_only=True)
    
    class Meta:
        model = Demand
        fields = [
            'id', 'publisher_username', 'title', 'demand_type',
            'budget', 'location', 'status', 'created_at', 'comment_count'
        ]


class DemandCommentSerializer(serializers.ModelSerializer):
    """需求评论序列化器"""
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_avatar = serializers.ImageField(source='creator.avatar', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    
    class Meta:
        model = DemandComment
        fields = [
            'id', 'demand', 'creator', 'creator_username', 'creator_avatar',
            'bid_price', 'message', 'status', 'created_at'
        ]
        read_only_fields = ['creator', 'status', 'created_at']
    
    def create(self, validated_data):
        """创建评论时，自动关联当前登录用户"""
        user = self.context['request'].user
        validated_data['creator'] = user
        
        # 检查是否已报价
        demand = validated_data['demand']
        if DemandComment.objects.filter(demand=demand, creator=user).exists():
            raise serializers.ValidationError("您已对该需求报价，无法重复报价")
        
        return super().create(validated_data)


class DemandDetailSerializer(DemandSerializer):
    """需求详情序列化器（包含评论）"""
    comments = DemandCommentSerializer(many=True, read_only=True)
    
    class Meta(DemandSerializer.Meta):
        fields = DemandSerializer.Meta.fields + ['comments']