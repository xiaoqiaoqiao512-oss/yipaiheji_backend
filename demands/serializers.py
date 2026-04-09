# demands/serializers.py
import json

from rest_framework import serializers
from .models import Demand, DemandComment
from users.models import User

class DemandSerializer(serializers.ModelSerializer):
    """需求序列化器"""
    publisher_username = serializers.CharField(source='publisher.username', read_only=True)
    publisher_avatar = serializers.ImageField(source='publisher.avatar', read_only=True)
    tags = serializers.JSONField(required=False, default=list)
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

    def validate_tags(self, value):
        """
        兼容前端多种传法：
        1) 字符串数组，如 ["毕业照"]
        2) 逗号分隔字符串，如 "毕业照,夜景"
        3) 标签 ID 数组，如 [1, 101]
        """
        if value is None:
            return []

        normalized = value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []

            if text.startswith('['):
                try:
                    normalized = json.loads(text)
                except json.JSONDecodeError:
                    normalized = [item.strip() for item in text.split(',') if item.strip()]
            else:
                normalized = [item.strip() for item in text.split(',') if item.strip()]

        if not isinstance(normalized, list):
            raise serializers.ValidationError("tags 必须是字符串或字符串数组")

        cleaned = []
        for item in normalized:
            if isinstance(item, bool):
                raise serializers.ValidationError("tags 元素不能是布尔值")

            if isinstance(item, int):
                cleaned.append(item)
                continue

            if isinstance(item, float):
                if not item.is_integer():
                    raise serializers.ValidationError("tags 数字标签必须为整数")
                cleaned.append(int(item))
                continue

            if isinstance(item, str):
                tag = item.strip()
                if not tag:
                    continue
                cleaned.append(int(tag) if tag.isdigit() else tag)
                continue

            raise serializers.ValidationError("tags 元素必须是字符串或数字")

        if not cleaned:
            raise serializers.ValidationError("请至少提供一个标签")

        return cleaned


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