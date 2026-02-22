from django.shortcuts import render

# demands/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Demand, DemandComment
from .serializers import (
    DemandSerializer, DemandListSerializer,
    DemandCommentSerializer, DemandDetailSerializer
)

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
