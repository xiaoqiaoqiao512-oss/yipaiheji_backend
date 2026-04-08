from django.db import transaction
from rest_framework import serializers
from .models import Equipment, EquipmentImage


class EquipmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentImage
        fields = ['id', 'image']


class EquipmentListSerializer(serializers.ModelSerializer):
    publisher_username = serializers.CharField(source='publisher.username', read_only=True)
    publisher_avatar = serializers.ImageField(source='publisher.avatar', read_only=True)
    publisher_is_verified = serializers.BooleanField(source='publisher.is_verified', read_only=True)
    publisher_is_creator = serializers.BooleanField(source='publisher.is_creator', read_only=True)
    publisher_creator_profile_id = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = [
            'id',
            'post_type',
            'category',
            'device_model',
            'rent_per_day',
            'deposit',
            'thumbnail',
            'publisher_username',
            'publisher_avatar',
            'publisher_is_verified',
            'publisher_is_creator',
            'publisher_creator_profile_id',
            'created_at',
        ]

    def get_thumbnail(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        return None

    def get_publisher_creator_profile_id(self, obj):
        profile = getattr(obj.publisher, 'creator_profile', None)
        if profile and obj.publisher.is_creator:
            return profile.id
        return None


class EquipmentDetailSerializer(EquipmentListSerializer):
    images = EquipmentImageSerializer(many=True, read_only=True)

    class Meta(EquipmentListSerializer.Meta):
        fields = EquipmentListSerializer.Meta.fields + [
            'description',
            'images',
            'updated_at',
        ]


class EquipmentCreateSerializer(serializers.ModelSerializer):
    publisher_username = serializers.CharField(source='publisher.username', read_only=True)
    upload_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    images = EquipmentImageSerializer(many=True, read_only=True)

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
            'upload_images',
            'images',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'publisher', 'publisher_username', 'status', 'images', 'created_at', 'updated_at']

    def validate(self, attrs):
        """兼容 multipart/form-data 的多文件上传"""
        request = self.context.get('request')
        if request:
            request_images = request.FILES.getlist('upload_images')
            if request_images:
                attrs['upload_images'] = request_images

        upload_images = attrs.get('upload_images', [])
        if len(upload_images) > 3:
            raise serializers.ValidationError({'upload_images': '最多上传3张图片'})

        return attrs

    def validate_upload_images(self, value):
        if len(value) > 3:
            raise serializers.ValidationError('最多上传3张图片')
        return value

    @transaction.atomic
    def create(self, validated_data):
        """创建设备信息时自动关联当前用户并保存图片"""
        upload_images = validated_data.pop('upload_images', [])
        validated_data['publisher'] = self.context['request'].user

        equipment = super().create(validated_data)
        for image in upload_images:
            EquipmentImage.objects.create(equipment=equipment, image=image)

        return equipment