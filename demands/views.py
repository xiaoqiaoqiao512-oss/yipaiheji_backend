# demands/views.py
from django.shortcuts import render

# rest_framework 相关
from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Case, When

# 模型与序列化器
from .models import Demand, DemandComment
from .serializers import (
    DemandSerializer, DemandListSerializer,
    DemandCommentSerializer, DemandDetailSerializer
)

# 创作者相关
from creators.models import CreatorProfile
from creators.serializers import CreatorPublicSerializer

# 图片上传所需
import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# drf-spectacular 文档
from drf_spectacular.utils import extend_schema, OpenApiResponse

# 日志
import logging
logger = logging.getLogger(__name__)


# ====== 需求列表与创建 ======
class DemandListCreateView(generics.ListCreateAPIView):
    """需求列表和创建"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DemandSerializer
        return DemandListSerializer
    
    def get_queryset(self):
        queryset = Demand.objects.all()
        
        # 查询参数过滤
        demand_type = self.request.query_params.get('type')
        location = self.request.query_params.get('location')
        status = self.request.query_params.get('status')
        min_budget = self.request.query_params.get('min_budget')
        max_budget = self.request.query_params.get('max_budget')
        
        if demand_type:
            queryset = queryset.filter(demand_type=demand_type)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if status:
            queryset = queryset.filter(status=status)
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)
        
        # 默认只显示待接单的需求
        if not status:
            queryset = queryset.filter(status='pending')
        
        # 为创作者按匹配度排序（SQLite 不可用，已忽略）
        for_creator = self.request.query_params.get('for_creator')
        if for_creator and self.request.user.is_authenticated:
            logger.warning("for_creator 排序在 SQLite 上不可用，已忽略，返回默认排序")
        
        return queryset.order_by('-created_at')


# ====== 需求详情、更新、删除 ======
class DemandDetailView(generics.RetrieveUpdateDestroyAPIView):
    """需求详情、更新、删除"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = DemandDetailSerializer
    queryset = Demand.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DemandDetailSerializer
        return DemandSerializer
    
    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.publisher != self.request.user:
            raise permissions.exceptions.PermissionDenied("只有发布者可以修改需求")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.publisher != self.request.user:
            raise permissions.exceptions.PermissionDenied("只有发布者可以删除需求")
        instance.delete()


# ====== 需求评论（报价） ======
class DemandCommentCreateView(generics.CreateAPIView):
    """创建需求评论（报价）"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DemandCommentSerializer
    queryset = DemandComment.objects.all()


class DemandCommentListView(generics.ListAPIView):
    """获取需求的评论列表"""
    permission_classes = [permissions.AllowAny]
    serializer_class = DemandCommentSerializer
    
    def get_queryset(self):
        demand_id = self.kwargs['demand_id']
        return DemandComment.objects.filter(demand_id=demand_id).order_by('created_at')


class AcceptCommentView(APIView):
    """接受创作者的报价"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, comment_id):
        comment = get_object_or_404(DemandComment, id=comment_id)
        demand = comment.demand
        
        if demand.publisher != request.user:
            return Response(
                {"error": "只有需求发布者可以接受报价"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if demand.status != 'pending':
            return Response(
                {"error": "该需求已被接单或已取消"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment.status = 'accepted'
        comment.save()
        
        demand.status = 'matched'
        demand.matched_creator = comment.creator
        demand.save()
        
        DemandComment.objects.filter(
            demand=demand, 
            status='pending'
        ).exclude(id=comment_id).update(status='rejected')
        
        return Response({
            "message": "已接受报价",
            "demand_id": demand.id,
            "creator_id": comment.creator.id,
            "creator_username": comment.creator.username
        })


# ====== 我的需求和报价 ======
class MyDemandsView(generics.ListAPIView):
    """获取当前用户发布的需求"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DemandListSerializer
    
    def get_queryset(self):
        return Demand.objects.filter(publisher=self.request.user).order_by('-created_at')


class MyBidsView(generics.ListAPIView):
    """获取当前用户的报价记录"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DemandCommentSerializer
    
    def get_queryset(self):
        return DemandComment.objects.filter(creator=self.request.user).order_by('-created_at')


# ====== 需求详情页推荐创作者 ======
class DemandRecommendedCreatorsView(APIView):
    """
    为指定需求推荐前5位匹配度最高的创作者。
    匹配规则：标签重合度 > 平均评分
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, demand_id):
        demand = get_object_or_404(Demand, id=demand_id)
        demand_tag_ids = set(demand.tags)

        if not demand_tag_ids:
            return Response([])

        all_creators = CreatorProfile.objects.all().select_related('user')
        creator_list = []
        for creator in all_creators:
            creator_tag_ids = set(creator.tags)
            common_tags = demand_tag_ids & creator_tag_ids
            if common_tags:
                match_count = len(common_tags)
                creator_list.append((creator, match_count))

        creator_list.sort(key=lambda x: (x[1], x[0].average_rating), reverse=True)
        top_creators = [c[0] for c in creator_list[:5]]

        serializer = CreatorPublicSerializer(top_creators, many=True, context={'request': request})
        return Response(serializer.data)


# ====== 新增：单张图片上传接口（供需求参考图使用） ======
class SingleImageUploadView(APIView):
    """
    单张图片上传（通用）
    前端可循环调用此接口，一次上传一张图，获得图片 URL 后存入需求对象的 reference_images 字段。
    """
    permission_classes = [permissions.IsAuthenticated]
    MAX_SIZE = 5 * 1024 * 1024          # 5MB
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '图片文件（JPEG/PNG，最大5MB）'
                    }
                },
                'required': ['image']
            }
        },
        responses={
            201: OpenApiResponse(
                description='上传成功，返回图片URL',
                response={'type': 'object', 'properties': {'url': {'type': 'string'}}}
            ),
            400: OpenApiResponse(description='请求错误（缺少文件、大小超限、格式不支持）'),
            401: OpenApiResponse(description='未认证'),
        },
        description='上传一张图片，返回图片URL。可连续调用最多3次，将返回的URL存入需求的 reference_images 字段。'
    )
    def post(self, request):
        file = request.FILES.get('image')
        if not file:
            return Response(
                {"error": "请上传图片，字段名为 'image'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if file.size > self.MAX_SIZE:
            return Response(
                {"error": f"图片大小不能超过 {self.MAX_SIZE // (1024*1024)}MB"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if file.content_type not in self.ALLOWED_TYPES:
            return Response(
                {"error": "仅支持 JPEG/PNG 格式"},
                status=status.HTTP_400_BAD_REQUEST
            )
        ext = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        sub_path = f"uploads/user_{request.user.id}/"
        full_path = default_storage.save(sub_path + filename, ContentFile(file.read()))
        url = request.build_absolute_uri(settings.MEDIA_URL + full_path)
        return Response({"url": url}, status=status.HTTP_201_CREATED)