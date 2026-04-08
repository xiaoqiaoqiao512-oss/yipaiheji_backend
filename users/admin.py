from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CreatorSampleImage

class CreatorSampleImageInline(admin.TabularInline):
    """样片内联显示，用于在用户详情页展示上传的样片"""
    model = CreatorSampleImage
    extra = 0  # 不显示额外的空行
    fields = ('image', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    can_delete = True
    max_num = 5  # 最多显示5张
    verbose_name = "样片"
    verbose_name_plural = "样片列表"

class CustomUserAdmin(UserAdmin):
    """自定义用户后台管理界面"""
    
    # 列表页显示的字段
    list_display = ('username', 'email', 'student_id', 'role', 
                    'is_verified', 'creator_application_status', 'is_active_creator', 'is_staff')
    
    # 可搜索的字段
    search_fields = ('username', 'student_id', 'email', 'phone')
    
    # 右侧过滤器
    list_filter = ('role', 'is_verified', 'creator_application_status', 
                   'is_active_creator', 'is_staff', 'is_superuser')
    
    # 详情页字段分组
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email', 'bio')}), 
        ('校园信息', {'fields': ('student_id', 'phone', 'avatar')}),
        ('创作者信息', {'fields': ('is_verified', 'student_card_img', 'tags')}),
        ('创作者申请状态', {'fields': ('creator_application_status', 'creator_applied_at')}),  
        ('创作者统计信息', {'fields': ('completed_orders', 'is_active_creator')}), 
        ('权限', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    
    # 添加用户时显示的字段
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'student_id', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    # 只读字段
    readonly_fields = ('creator_applied_at',)
    
    # 添加内联样片显示
    inlines = [CreatorSampleImageInline]

# 注册 CreatorSampleImage 模型的管理类（可选，但建议注册以独立管理）
@admin.register(CreatorSampleImage)
class CreatorSampleImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('user__username', 'user__student_id')
    raw_id_fields = ('user',)  # 便于按用户搜索
    readonly_fields = ('uploaded_at',)

# 注册自定义用户模型和管理类
admin.site.register(User, CustomUserAdmin)
