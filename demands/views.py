from django.shortcuts import render

# demands/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Case, When  # 新增导入 Case, When
from .models import Demand, DemandComment
from .serializers import (
    DemandSerializer, DemandListSerializer,
    DemandCommentSerializer, DemandDetailSerializer
)

# ====== 新增导入：创作者相关 ======
from creators.models import CreatorProfile
from creators.serializers import CreatorPublicSerializer

# 导入日志
import logging

logger = logging.getLogger(__name__)

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
        
        # ====== 新增：为创作者按匹配度排序（for_creator 参数）======
        for_creator = self.request.query_params.get('for_creator')
        if for_creator and self.request.user.is_authenticated:
            # SQLite 不支持 JSONField 的 contains 查询，暂时禁用该功能
            # 记录日志提示，并返回默认排序
            logger.warning("for_creator 排序在 SQLite 上不可用，已忽略，返回默认排序")
            # 不做任何处理，直接返回现有 queryset
            pass
        
        return queryset.order_by('-created_at')


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
        """更新需求时，只能由发布者更新"""
        instance = self.get_object()
        if instance.publisher != self.request.user:
            raise permissions.exceptions.PermissionDenied("只有发布者可以修改需求")
        serializer.save()
    
    def perform_destroy(self, instance):
        """删除需求时，只能由发布者删除"""
        if instance.publisher != self.request.user:
            raise permissions.exceptions.PermissionDenied("只有发布者可以删除需求")
        instance.delete()


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
        
        # 检查权限：只有需求发布者可以接受报价
        if demand.publisher != request.user:
            return Response(
                {"error": "只有需求发布者可以接受报价"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查需求状态
        if demand.status != 'pending':
            return Response(
                {"error": "该需求已被接单或已取消"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新评论状态为已接受
        comment.status = 'accepted'
        comment.save()
        
        # 更新需求状态和匹配的创作者
        demand.status = 'matched'
        demand.matched_creator = comment.creator
        demand.save()
        
        # 拒绝其他报价
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


# ====== 新增：需求详情页推荐创作者接口 ======
class DemandRecommendedCreatorsView(APIView):
    """
    为指定需求推荐前5位匹配度最高的创作者。
    匹配规则：标签重合度 > 平均评分
    GET /demands/{demand_id}/recommended_creators/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, demand_id):
        demand = get_object_or_404(Demand, id=demand_id)
        demand_tag_ids = set(demand.tags)  # 需求标签ID集合

        if not demand_tag_ids:
            return Response([])  # 需求无标签，无法推荐

        # 获取所有创作者（可添加额外过滤条件，如只获取有标签的创作者）
        all_creators = CreatorProfile.objects.all().select_related('user')

        # 在 Python 中计算匹配度（因为 SQLite 不支持 JSONField 的 contains 查询）
        creator_list = []
        for creator in all_creators:
            creator_tag_ids = set(creator.tags)
            common_tags = demand_tag_ids & creator_tag_ids
            if common_tags:  # 只考虑有共同标签的创作者
                match_count = len(common_tags)
                creator_list.append((creator, match_count))

        # 按匹配数降序，同分按平均评分降序
        creator_list.sort(key=lambda x: (x[1], x[0].average_rating), reverse=True)
        top_creators = [c[0] for c in creator_list[:5]]

        serializer = CreatorPublicSerializer(top_creators, many=True, context={'request': request})
        return Response(serializer.data)
