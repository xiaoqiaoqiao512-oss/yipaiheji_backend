from django.contrib import admin
from .models import CreatorProfile, Work

# 注册创作者档案和作品模型
admin.site.register(CreatorProfile)
admin.site.register(Work)

from .models import CreatorProfile, Work, Service  # 添加Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """服务项目后台管理"""
    list_display = ['creator', 'name', 'base_price', 'is_available', 'order_count']
    search_fields = ['name', 'creator__username']
    list_filter = ['is_available', 'is_negotiable']
