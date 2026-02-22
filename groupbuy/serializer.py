from rest_framework import serializers
from .models import GroupBuy, GroupBuyMember
from users.models import User


class GroupBuyMemberSerializer(serializers.ModelSerializer):
    """拼单成员序列化器（用于返回成员列表）"""
    
    # 返回成员的用户名和头像
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    
    class Meta:
        model = GroupBuyMember
        fields = ['user', 'username', 'avatar', 'joined_at']
        read_only_fields = ['joined_at']


class GroupBuySerializer(serializers.ModelSerializer):
    """拼单详情序列化器"""
    
    # 发起者信息
    initiator_username = serializers.CharField(source='initiator.username', read_only=True)
    initiator_avatar = serializers.ImageField(source='initiator.avatar', read_only=True)
    
    # 成员列表（嵌套序列化）
    # 前端访问 /groupbuy/{id}/ 时会看到完整的成员列表
    members = GroupBuyMemberSerializer(many=True, read_only=True)
    
    # 计算字段（不存在于数据库，但前端需要）
    current_people_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupBuy
        fields = [
            'id',
            'initiator',
            'initiator_username',
            'initiator_avatar',
            'title',
            'description',
            'target_people_count',
            'current_people_count',
            'cost_per_person',
            'status',
            'is_full',
            'created_at',
            'updated_at',
            'members',
        ]
        read_only_fields = [
            'initiator',
            'initiator_username',
            'initiator_avatar',
            'status',
            'created_at',
            'updated_at',
            'current_people_count',
            'is_full',
            'members',
        ]

    def get_current_people_count(self, obj):
        """调用 model 的方法返回当前人数"""
        return obj.get_current_members_count()

    def get_is_full(self, obj):
        """调用 model 的方法返回是否满员"""
        return obj.is_full()

    def create(self, validated_data):
        """发布拼单时，自动关联当前登录用户为发起者"""
        validated_data['initiator'] = self.context['request'].user
        return super().create(validated_data)


class GroupBuyListSerializer(serializers.ModelSerializer):
    """拼单列表序列化器（简化版，只返回关键字段）"""
    
    initiator_username = serializers.CharField(source='initiator.username', read_only=True)
    current_people_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupBuy
        fields = [
            'id',
            'initiator_username',
            'title',
            'target_people_count',
            'current_people_count',
            'cost_per_person',
            'status',
            'is_full',
            'created_at',
        ]

    def get_current_people_count(self, obj):
        return obj.get_current_members_count()

    def get_is_full(self, obj):
        return obj.is_full()