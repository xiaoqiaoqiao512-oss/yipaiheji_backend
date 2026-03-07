# creators/serializers.py
from rest_framework import serializers
from .models import CreatorProfile, Work, Service, Location, WorkLike, Comment, Favorite, WorkImage
from users.models import User
from .tag_choices import is_valid_tag_id, TAGS

class WorkImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkImage
        fields = ['id', 'image', 'order']



class WorkImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkImage
        fields = ['id', 'image', 'order']


class WorkSerializer(serializers.ModelSerializer):
    """作品序列化器"""
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    creator_avatar = serializers.ImageField(source='creator.avatar', read_only=True)

    # 地点相关
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_detail = serializers.SerializerMethodField(read_only=True)

    # 互动字段
    is_liked = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    recent_comments = serializers.SerializerMethodField(read_only=True)

    # 作品集中的图片列表
    images = WorkImageSerializer(many=True, read_only=True)

    class Meta:
        model = Work
        fields = [
            'id', 'creator', 'creator_username', 'creator_avatar',
            'title', 'image', 'description', 'tags', 'shooting_location',
            'location', 'location_name', 'location_detail',
            'like_count', 'view_count', 'is_public', 'created_at',
            'is_liked', 'is_favorited', 'comment_count', 'recent_comments',
            'display_order', 'image', 'images' 
        ]
        read_only_fields = ['like_count', 'view_count', 'created_at']

    def get_location_detail(self, obj):
        if obj.location:
            return {
                'id': obj.location.id,
                'name': obj.location.name,
                'longitude': float(obj.location.longitude),
                'latitude': float(obj.location.latitude),
                'description': obj.location.description,
                'category': obj.location.category,
            }
        return None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return WorkLike.objects.filter(user=request.user, work=obj).exists()
        return False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, work=obj).exists()
        return False

    def get_recent_comments(self, obj):
        comments = obj.comments.filter(is_deleted=False).order_by('-created_at')[:3]
        return CommentSerializer(comments, many=True, context=self.context).data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['creator'] = user
        return super().create(validated_data)

    # ===== 新增：tags 字段验证 =====
    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("标签必须是一个列表")
        for tag_id in value:
            if not isinstance(tag_id, int):
                raise serializers.ValidationError("标签ID必须是整数")
            if not is_valid_tag_id(tag_id):
                raise serializers.ValidationError(f"无效的标签ID: {tag_id}")
        return value


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

    # ===== 新增：tags 字段验证 =====
    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("标签必须是一个列表")
        for tag_id in value:
            if not isinstance(tag_id, int):
                raise serializers.ValidationError("标签ID必须是整数")
            if not is_valid_tag_id(tag_id):
                raise serializers.ValidationError(f"无效的标签ID: {tag_id}")
        return value


class CreatorProfileSerializer(serializers.ModelSerializer):
    """创作者档案序列化器"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    student_id = serializers.CharField(source='user.student_id', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    # ===== 新增：tags 字段 =====
    tags = serializers.JSONField(required=False, default=list)

    class Meta:
        model = CreatorProfile
        fields = ['id', 'user_id', 'username', 'student_id', 'avatar',
                  'service_intro', 'base_price', 'price_range', 'is_negotiable',
                  'camera_model', 'can_provide_makeup', 'can_provide_costume',
                  'completed_orders', 'average_rating', 'view_count',
                  'tags',  # 新增
                  'created_at', 'updated_at']
        read_only_fields = ['completed_orders', 'average_rating', 'view_count',
                           'created_at', 'updated_at']

    # ===== 新增：tags 字段验证 =====
    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("标签必须是一个列表")
        for tag_id in value:
            if not isinstance(tag_id, int):
                raise serializers.ValidationError("标签ID必须是整数")
            if not is_valid_tag_id(tag_id):
                raise serializers.ValidationError(f"无效的标签ID: {tag_id}")
        return value


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
    # 创作者标签
    tags = serializers.JSONField(required=False)

    class Meta:
        model = CreatorProfile
        fields = ['id', 'username', 'avatar', 'service_intro',
                  'base_price', 'average_rating', 'completed_orders',
                  'work_count', 'recent_works', 'services', 'tags']  # tags 已在其中

    def get_work_count(self, obj):
        """获取作品数量"""
        return obj.user.works.filter(is_public=True).count()

    def get_recent_works(self, obj):
        """获取最近3个公开作品"""
        works = obj.user.works.filter(is_public=True).order_by('-created_at')[:3]
        return WorkSerializer(works, many=True, context=self.context).data

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("标签必须是一个列表")
        for tag_id in value:
            if not isinstance(tag_id, int) or not is_valid_tag_id(tag_id):
                raise serializers.ValidationError(f"无效的标签ID: {tag_id}")
        return value


# ========== 新增：地点相关序列化器 ==========

class LocationListSerializer(serializers.ModelSerializer):
    """地点列表序列化器（用于全校地图）"""
    work_count = serializers.IntegerField(read_only=True)
    cover_image = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Location
        fields = ['id', 'name', 'longitude', 'latitude', 'description',
                  'category', 'campus', 'work_count', 'cover_image']


class MyLocationSerializer(serializers.ModelSerializer):
    """我的地图地点序列化器（包含用户作品缩略图）"""
    work_count = serializers.IntegerField(read_only=True)
    user_works = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'longitude', 'latitude', 'work_count', 'user_works']

    def get_user_works(self, obj):
        # 从视图传递的 context 中获取该地点的用户作品预览
        if hasattr(obj, 'user_works_preview'):
            return obj.user_works_preview
        return []


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'username', 'user_avatar', 'work', 'content', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['work', 'content']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    work_detail = WorkSerializer(source='work', read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'work', 'work_detail', 'created_at']
        read_only_fields = ['user', 'created_at']