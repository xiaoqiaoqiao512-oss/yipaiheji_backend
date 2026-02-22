from django.contrib import admin
from .models import Demand, DemandComment

@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    """需求后台管理"""
    list_display = ['title', 'publisher', 'demand_type', 'budget', 'status', 'created_at']
    search_fields = ['title', 'publisher__username', 'description']
    list_filter = ['demand_type', 'status', 'created_at']
    readonly_fields = ['view_count', 'comment_count']
    date_hierarchy = 'created_at'

@admin.register(DemandComment)
class DemandCommentAdmin(admin.ModelAdmin):
    """需求评论后台管理"""
    list_display = ['demand', 'creator', 'bid_price', 'status', 'created_at']
    search_fields = ['demand__title', 'creator__username']
    list_filter = ['status', 'created_at']
