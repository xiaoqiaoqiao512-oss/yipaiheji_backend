# users/serializers.py
from rest_framework import serializers
from .models import User, CreatorSampleImage
from django.contrib.auth.hashers import make_password

class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'student_id', 'phone', 'password', 'confirm_password']
    
    def validate(self, data):
        """验证两次密码是否一致"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "两次密码不一致"})
        
        # 检查学号是否已存在
        if User.objects.filter(student_id=data['student_id']).exists():
            raise serializers.ValidationError({"student_id": "该学号已注册"})
        
        # 检查用户名是否已存在
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "用户名已存在"})
        
        return data
    
    def create(self, validated_data):
        """创建用户"""
        # 移除确认密码字段
        validated_data.pop('confirm_password')
        
        # 创建用户，密码加密存储
        user = User.objects.create(
            username=validated_data['username'],
            student_id=validated_data['student_id'],
            phone=validated_data.get('phone', ''),
            password=make_password(validated_data['password']),
            role='student'  # 默认注册为学生
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    # 添加计算属性字段
    is_creator = serializers.BooleanField(read_only=True)
    display_role = serializers.CharField(read_only=True)
    # 新增：样片 URL 列表（只读）
    sample_images = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'student_id', 'phone', 'role', 
            'avatar', 'is_verified', 'bio', 'tags',
            # 新增字段
            'creator_application_status', 'creator_applied_at',
            'completed_orders', 'is_active_creator',
            # 学生卡照片（用于校园认证）
            'student_card_img',
            # 计算属性
            'is_creator', 'display_role',
            'created_at',
            # 样片字段
            'sample_images',
        ]
        read_only_fields = [
            'id', 'role', 'is_verified', 'created_at',
            'creator_application_status', 'creator_applied_at',  # 这些字段不能直接修改
            'completed_orders', 'is_active_creator',
            'student_card_img',  # 学生卡照片设为只读，防止通过此接口修改
            'is_creator', 'display_role',  # 计算属性也是只读的
            'sample_images',  # 样片字段只读
        ]
    
    def get_sample_images(self, obj):
        """返回当前用户所有样片的绝对 URL 列表"""
        request = self.context.get('request')
        if not request:
            return []
        # 使用 related_name 'sample_images' 获取所有样片
        return [request.build_absolute_uri(img.image.url) for img in obj.sample_images.all()]
    
    def update(self, instance, validated_data):
        """更新用户信息"""
        # 可以更新的字段
        updatable_fields = ['phone', 'avatar', 'bio', 'tags']
        
        for field in updatable_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance


class StudentCardUploadSerializer(serializers.ModelSerializer):
    """学生卡照片上传序列化器（仅用于上传）"""
    class Meta:
        model = User
        fields = ['student_card_img']
        # 这里不设置 read_only，因为需要允许写入


class CreatorApplySerializer(serializers.Serializer):
    """创作者申请序列化器（用于接收样片文件，数量 2~5 张）"""
    sample_images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=2,
        max_length=5,
        write_only=True,
        help_text="上传 2-5 张样片图片"
    )

    def validate_sample_images(self, value):
        """可选：进一步校验每张图片的大小、格式等"""
        for img in value:
            # 限制单张图片最大 5MB
            if img.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(f"图片 {img.name} 大小超过 5MB")
            # 可选：限制图片格式
            if not img.content_type.startswith('image/'):
                raise serializers.ValidationError(f"文件 {img.name} 不是有效的图片格式")
        return value