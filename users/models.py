from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """自定义用户模型，扩展Django内置用户"""
    
    # 用户角色选择
    ROLE_CHOICES = [
        ('student', '普通学生'),
        ('creator', '创作者'),
        ('admin', '管理员'),
    ]
    
    # 基础信息
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField('学号', max_length=20, blank=True, null=True)
    phone = models.CharField('手机号', max_length=15, blank=True, null=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    
    # 创作者认证相关
    is_verified = models.BooleanField('是否认证', default=False)
    student_card_img = models.ImageField('学生卡照片', upload_to='student_cards/', blank=True, null=True)
    tags = models.JSONField('标签', default=list, blank=True)  # 存储标签列表，如["人像", "夜景"]
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'users'  # 数据库表名
        verbose_name = '用户'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.username} ({self.student_id or '无学号'})"