# users/serializers.py
from rest_framework import serializers
from .models import User
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
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'student_id', 'phone', 'role', 
            'avatar', 'is_verified', 'bio', 'tags',
            # 新增字段
            'creator_application_status', 'creator_applied_at',
            'completed_orders', 'is_active_creator',
            # 计算属性
            'is_creator', 'display_role',
            'created_at'
        ]
        read_only_fields = [
            'id', 'role', 'is_verified', 'created_at',
            'creator_application_status', 'creator_applied_at',  # 这些字段不能直接修改
            'completed_orders', 'is_active_creator',
            'is_creator', 'display_role'  # 计算属性也是只读的
        ]
    
    def update(self, instance, validated_data):
        """更新用户信息"""
        # 可以更新的字段
        updatable_fields = ['phone', 'avatar', 'bio', 'tags']
        
        for field in updatable_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance