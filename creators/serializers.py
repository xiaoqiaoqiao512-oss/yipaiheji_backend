# creators/serializers.py
from rest_framework import serializers
from .models import CreatorProfile, Work, Service
from users.models import User

class WorkSerializer(serializers.ModelSerializer):
    """作品序列化器"""
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_avatar = serializers.ImageField(source='creator.avatar', read_only=True)
    
    class Meta:
        model = Work
        fields = ['id', 'creator', 'creator_username', 'creator_avatar', 
                  'title', 'image', 'description', 'tags', 'shooting_location',
                  'like_count', 'view_count', 'is_public', 'created_at']
        read_only_fields = ['like_count', 'view_count', 'created_at']
    
    def create(self, validated_data):
        """创建作品时，自动关联当前登录用户"""
        user = self.context['request'].user
        validated_data['creator'] = user
        return super().create(validated_data)


class ServiceSerializer(serializers.ModelSerializer):
    """服务项目序列化器"""
    
    class Meta:
        model = Service
        fields = ['id', 'creator', 'name', 'description', 'base_price', 
                  'price_range', 'estimated_time', 'is_negotiable', 
                  'is_available', 'tags', 'order_count', 'created_at']
        read_only_fields = ['order_count', 'created_at']
    
    def create(self, validated_data):
        """创建服务时，自动关联当前登录用户"""
        user = self.context['request'].user
        validated_data['creator'] = user
        return super().create(validated_data)


class CreatorProfileSerializer(serializers.ModelSerializer):
    """创作者档案序列化器"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    student_id = serializers.CharField(source='user.student_id', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    
    class Meta:
        model = CreatorProfile
        fields = ['id', 'user_id', 'username', 'student_id', 'avatar',
                  'service_intro', 'base_price', 'price_range', 'is_negotiable',
                  'camera_model', 'can_provide_makeup', 'can_provide_costume',
                  'completed_orders', 'average_rating', 'view_count', 
                  'created_at', 'updated_at']
        read_only_fields = ['completed_orders', 'average_rating', 'view_count', 
                           'created_at', 'updated_at']


class CreatorPublicSerializer(serializers.ModelSerializer):
    """创作者公开信息序列化器（供需求方查看）"""
    username = serializers.CharField(source='user.username')
    avatar = serializers.ImageField(source='user.avatar')
    
    # 统计作品数量
    work_count = serializers.SerializerMethodField()
    # 获取前3个作品
    recent_works = serializers.SerializerMethodField()
    # 获取服务列表
    services = ServiceSerializer(many=True, read_only=True, source='user.services')
    
    class Meta:
        model = CreatorProfile
        fields = ['id', 'username', 'avatar', 'service_intro', 
                  'base_price', 'average_rating', 'completed_orders',
                  'work_count', 'recent_works', 'services']
    
    def get_work_count(self, obj):
        """获取作品数量"""
        return obj.user.works.filter(is_public=True).count()
    
    def get_recent_works(self, obj):
        """获取最近3个公开作品"""
        works = obj.user.works.filter(is_public=True).order_by('-created_at')[:3]
        return WorkSerializer(works, many=True, context=self.context).data