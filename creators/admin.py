from django.contrib import admin
from .models import CreatorProfile, Work, WorkImage, Service

class WorkImageInline(admin.TabularInline):
    """作品图片内联管理"""
    model = WorkImage
    extra = 1  # 显示一个空的上传框
    fields = ['image', 'order']
    ordering = ['order']

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    """作品管理"""
    list_display = ['id', 'creator', 'title', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'creator__username']
    inlines = [WorkImageInline]  # 关键：必须包含内联

@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'base_price', 'completed_orders', 'average_rating']
    search_fields = ['user__username']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['creator', 'name', 'base_price', 'is_available', 'order_count']
    search_fields = ['name', 'creator__username']
    list_filter = ['is_available', 'is_negotiable']


