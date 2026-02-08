from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    """自定义用户后台管理界面"""
    
    # 列表页显示的字段
    list_display = ('username', 'email', 'student_id', 'role', 'is_verified', 'is_staff')
    
    # 可搜索的字段
    search_fields = ('username', 'student_id', 'email', 'phone')
    
    # 右侧过滤器
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser')
    
    # 详情页字段分组 - 非常重要！这决定了添加/编辑用户时显示哪些字段
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('校园信息', {'fields': ('student_id', 'phone', 'avatar')}),
        ('创作者信息', {'fields': ('is_verified', 'student_card_img', 'tags')}),
        ('权限', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    
    # 添加用户时显示的字段（比编辑时少）
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'student_id', 'email','password1', 'password2', 'role'),
        }),
    )

# 注册自定义用户模型和管理类
admin.site.register(User, CustomUserAdmin)
