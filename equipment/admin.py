from django.contrib import admin
from .models import Equipment, EquipmentImage


class EquipmentImageInline(admin.TabularInline):
    model = EquipmentImage
    extra = 0


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_model', 'post_type', 'category', 'rent_per_day', 'status', 'publisher', 'created_at')
    list_filter = ('post_type', 'category', 'status', 'created_at')
    search_fields = ('device_model', 'publisher__username')
    inlines = [EquipmentImageInline]


@admin.register(EquipmentImage)
class EquipmentImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment', 'created_at')
    search_fields = ('equipment__device_model',)
