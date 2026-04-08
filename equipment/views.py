from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from chat.models import Message
from .models import Equipment
from .serializer import EquipmentListSerializer, EquipmentDetailSerializer, EquipmentCreateSerializer


class EquipmentPostListCreateView(generics.ListCreateAPIView):
    """
    设备信息列表和创建
    GET: 浏览列表
    POST: 发布设备信息
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EquipmentCreateSerializer
        return EquipmentListSerializer
    
    def get_queryset(self):
        queryset = Equipment.objects.filter(status='active').select_related('publisher').prefetch_related('images').order_by('-created_at')

        post_type = self.request.query_params.get('post_type')
        category = self.request.query_params.get('category')

        if post_type:
            queryset = queryset.filter(post_type=post_type)
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset



class EquipmentPostDetailView(generics.RetrieveAPIView):
    """
    设备信息详情
    GET: 获取详情
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = EquipmentDetailSerializer

    def get_queryset(self):
        return Equipment.objects.filter(status='active').select_related('publisher').prefetch_related('images')


class ContactPublisherView(APIView):
    """
    联系发布者
    POST: 自动发送设备咨询私信
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        equipment = get_object_or_404(
            Equipment.objects.select_related('publisher'),
            pk=pk,
            status='active'
        )

        if equipment.publisher_id == request.user.id:
            return Response({'detail': '不能联系自己发布的设备'}, status=status.HTTP_400_BAD_REQUEST)

        content = (request.data.get('content') or '').strip()
        if len(content) > 500:
            return Response({'detail': '消息内容不能超过500字'}, status=status.HTTP_400_BAD_REQUEST)

        if not content:
            content = (
                f"你好，我想咨询你发布的设备：{equipment.device_model}。"
                f" 日租金：{equipment.rent_per_day} 元/天，押金：{equipment.deposit or '面议'}。"
            )

        message = Message.objects.create(
            sender=request.user,
            receiver=equipment.publisher,
            message_type='private',
            content=content,
        )

        return Response({
            'message': '已向发布者发送私信',
            'equipment_id': equipment.id,
            'receiver_id': equipment.publisher_id,
            'chat_message_id': message.id,
        }, status=status.HTTP_201_CREATED)


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
