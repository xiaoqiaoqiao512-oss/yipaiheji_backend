from rest_framework import serializers
from .models import Equipment

class EquipmentSerializer(serializers.ModelSerializer):
    publisher_username = serializers.CharField(source='publisher.username', read_only=True)

    class Meta:
        model = Equipment
        fields = [
            'id',
            'publisher',
            'publisher_username',
            'post_type',
            'category',
            'device_model',
            'rent_per_day',
            'deposit',
            'description',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'publisher', 'created_at', 'status', 'updated_at']
    
    def create(self, validated_data):
        """创建设备信息时自动关联当前用户为发布者"""
        validated_data['publisher'] = self.context['request'].user
        return super().create(validated_data)