from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Equipment
from .serializer import EquipmentSerializer


class EquipmentPostListCreateView(generics.ListCreateAPIView):
    """
    设备信息列表和创建
    GET: 浏览列表
    POST: 发布设备信息
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Equipment.objects.filter(status='active').order_by('-created_at')

        post_type = self.request.query_params.get('post_type')
        category = self.request.query_params.get('category')

        if post_type:
            queryset = queryset.filter(post_type=post_type)
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset

    serializer_class = EquipmentSerializer

    def perform_create(self, serializer):
        """发布时自动设置发布者"""
        serializer.save(publisher=self.request.user)


class RiskTipsView(APIView):
    """
    发布页风险提示
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "risk_notice": "平台仅提供信息发布，交易风险由双方线下协商承担",
            "recommended_process": [
                "线下验机",
                "签订借条",
                "押金通过第三方保管"
            ]
        })
