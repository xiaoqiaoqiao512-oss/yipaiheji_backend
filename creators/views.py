from django.shortcuts import render
# creators/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import CreatorProfile, Work, Service
from .serializers import (
    WorkSerializer, ServiceSerializer, 
    CreatorProfileSerializer, CreatorPublicSerializer
)
from users.models import User

# ========== 添加权限控制 ==========
class IsCreator(permissions.BasePermission):
    """只有创作者可以访问"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_creator
# ========== 权限控制结束 ==========

class CreatorProfileView(APIView):
    """获取或更新创作者个人档案"""
    permission_classes = [IsCreator]  # 只有创作者可以访问
    
    def get(self, request):
        """获取当前登录创作者的档案"""
        try:
            profile = request.user.creator_profile
            serializer = CreatorProfileSerializer(profile)
            return Response(serializer.data)
        except CreatorProfile.DoesNotExist:
            return Response(
                {"error": "您还不是创作者，请先申请认证"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """更新创作者档案"""
        try:
            profile = request.user.creator_profile
        except CreatorProfile.DoesNotExist:
            return Response(
                {"error": "您还不是创作者，无法更新档案"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CreatorProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatorPublicView(generics.RetrieveAPIView):
    """获取创作者公开信息（所有人都可以访问）"""
    permission_classes = [permissions.AllowAny]
    serializer_class = CreatorPublicSerializer
    queryset = CreatorProfile.objects.all()
    lookup_field = 'id'


class WorkListCreateView(generics.ListCreateAPIView):
    """作品列表和创建"""
    permission_classes = [IsCreator]  # 只有创作者可以访问
    serializer_class = WorkSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """只返回当前用户的作品"""
        return Work.objects.filter(creator=self.request.user)
    
    def perform_create(self, serializer):
        """创建作品时自动关联当前用户，并检查作品数量"""
        # 作品数量限制：最多20个
        current_count = Work.objects.filter(creator=self.request.user).count()
        if current_count >= 20:
            from rest_framework import serializers
            raise serializers.ValidationError({"error": "每个创作者最多只能上传20个作品"})
        
        serializer.save(creator=self.request.user)


class WorkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """作品详情、更新、删除"""
    permission_classes = [IsCreator]  # 只有创作者可以访问
    serializer_class = WorkSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """只允许用户操作自己的作品"""
        return Work.objects.filter(creator=self.request.user)


class ServiceListCreateView(generics.ListCreateAPIView):
    """服务项目列表和创建"""
    permission_classes = [IsCreator]  # 只有创作者可以访问
    serializer_class = ServiceSerializer
    
    def get_queryset(self):
        """只返回当前用户的服务项目"""
        return Service.objects.filter(creator=self.request.user)
    
    def perform_create(self, serializer):
        """创建服务时自动关联当前用户"""
        serializer.save(creator=self.request.user)


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """服务项目详情、更新、删除"""
    permission_classes = [IsCreator]  # 只有创作者可以访问
    serializer_class = ServiceSerializer
    
    def get_queryset(self):
        """只允许用户操作自己的服务项目"""
        return Service.objects.filter(creator=self.request.user)


class PublicWorksView(generics.ListAPIView):
    """公开作品墙（所有人都可以访问）"""
    permission_classes = [permissions.AllowAny]
    serializer_class = WorkSerializer
    
    def get_queryset(self):
        """只返回公开的作品"""
        return Work.objects.filter(is_public=True).order_by('-created_at')


# ========== 添加作品排序功能 ==========
class ReorderWorksView(APIView):
    """重新排序作品（拖拽排序）"""
    permission_classes = [IsCreator]
    
    def put(self, request):
        """批量更新作品顺序"""
        # 期望的数据格式: [{"id": 1, "display_order": 0}, {"id": 2, "display_order": 1}, ...]
        order_data = request.data.get('order', [])
        
        if not isinstance(order_data, list):
            return Response(
                {"error": "数据格式错误，应为列表"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证所有作品都属于当前用户
        work_ids = [item['id'] for item in order_data if 'id' in item]
        user_works = Work.objects.filter(creator=request.user, id__in=work_ids)
        
        if len(user_works) != len(order_data):
            return Response(
                {"error": "包含不属于您的作品"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 批量更新顺序
        for item in order_data:
            work_id = item.get('id')
            display_order = item.get('display_order')
            
            if work_id is not None and display_order is not None:
                Work.objects.filter(id=work_id, creator=request.user).update(
                    display_order=display_order
                )
        
        return Response({
            "message": "作品顺序已更新",
            "count": len(order_data)
        })


class UpdateWorkOrderView(APIView):
    """更新单个作品的顺序"""
    permission_classes = [IsCreator]
    
    def patch(self, request, pk):
        """更新指定作品的display_order"""
        try:
            work = Work.objects.get(id=pk, creator=request.user)
        except Work.DoesNotExist:
            return Response(
                {"error": "作品不存在或无权访问"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_order = request.data.get('display_order')
        if new_order is None:
            return Response(
                {"error": "必须提供display_order字段"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_order = int(new_order)
        except ValueError:
            return Response(
                {"error": "display_order必须是整数"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        work.display_order = new_order
        work.save()
        
        return Response({
            "id": work.id,
            "title": work.title,
            "display_order": work.display_order
        })
