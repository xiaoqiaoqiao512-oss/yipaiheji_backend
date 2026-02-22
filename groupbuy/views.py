from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import GroupBuy, GroupBuyMember
from .serializer import GroupBuySerializer, GroupBuyListSerializer


class GroupBuyListCreateView(generics.ListCreateAPIView):
    """
    GET: 浏览拼单列表
    POST: 发布拼单
    """
    serializer_class = GroupBuyListSerializer

    def get_permissions(self):
        # 浏览允许任何人，发布要求登录
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # 只显示"招人中"的拼单，按最新优先
        queryset = GroupBuy.objects.filter(status='recruiting').order_by('-created_at')
        
        # 可选筛选：按最低成本
        max_cost = self.request.query_params.get('max_cost')
        if max_cost:
            queryset = queryset.filter(cost_per_person__lte=max_cost)
        
        return queryset

    def perform_create(self, serializer):
        """发布拼单时自动绑定发起者"""
        serializer.save(initiator=self.request.user)


class GroupBuyDetailView(generics.RetrieveUpdateAPIView):
    """
    GET: 获取拼单详情（包括已加入成员）
    PUT/PATCH: 发起者可以修改拼单信息
    """
    serializer_class = GroupBuySerializer
    permission_classes = [permissions.AllowAny]  # 详情页任何人可看
    queryset = GroupBuy.objects.all()

    def perform_update(self, serializer):
        """只允许发起者修改拼单"""
        if serializer.instance.initiator != self.request.user:
            raise permissions.exceptions.PermissionDenied("只有发起者可以修改拼单")
        serializer.save()


class JoinGroupBuyView(APIView):
    """加入拼单"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # 获取拼单对象
        groupbuy = get_object_or_404(GroupBuy, pk=pk)

        # 检查1：拼单是否已满员
        if groupbuy.is_full():
            return Response(
                {"error": "拼单已满员"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查2：用户是否已加入
        if groupbuy.members.filter(user=request.user).exists():
            return Response(
                {"error": "你已加入此拼单"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查3：用户不能加入自己发起的拼单
        if groupbuy.initiator == request.user:
            return Response(
                {"error": "不能加入自己发起的拼单"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建成员关系
        GroupBuyMember.objects.create(groupbuy=groupbuy, user=request.user)

        # 如果加入后满员，自动改状态为 full
        if groupbuy.is_full():
            groupbuy.status = 'full'
            groupbuy.save()

        return Response(
            {"message": "加入成功"},
            status=status.HTTP_201_CREATED
        )


class LeaveGroupBuyView(APIView):
    """退出拼单"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        groupbuy = get_object_or_404(GroupBuy, pk=pk)

        # 防止发起者退出（拼单就废了）
        if groupbuy.initiator == request.user:
            return Response(
                {"error": "发起者不能退出拼单"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 删除成员关系
        member = groupbuy.members.filter(user=request.user).first()
        if not member:
            return Response(
                {"error": "你未加入此拼单"},
                status=status.HTTP_404_NOT_FOUND
            )

        member.delete()

        # 如果退出后不再满员，改状态回 recruiting
        if groupbuy.status == 'full' and not groupbuy.is_full():
            groupbuy.status = 'recruiting'
            groupbuy.save()

        return Response({"message": "已退出拼单"})