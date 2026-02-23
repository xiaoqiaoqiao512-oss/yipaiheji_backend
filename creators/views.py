from django.shortcuts import render
# creators/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, OuterRef, Subquery, Max
from .models import CreatorProfile, Work, WorkImage, Service, Location, WorkLike, Comment, Favorite
from .serializers import (
    WorkSerializer, ServiceSerializer,
    CreatorProfileSerializer, CreatorPublicSerializer,
    LocationListSerializer, MyLocationSerializer,
    CommentSerializer, CommentCreateSerializer,
    FavoriteSerializer, WorkImageSerializer
)
from users.models import User
# ====== 新增导入：标签常量 ======
from .tag_choices import TAGS, CATEGORY_SCENE, CATEGORY_SKILL, CATEGORY_SPECIAL, CATEGORY_POST

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
        """只返回当前用户的作品，按 display_order 排序"""
        return Work.objects.filter(creator=self.request.user).order_by('display_order', '-created_at')
    
    def create(self, request, *args, **kwargs):
        # 1. 检查作品数量限制
        current_count = Work.objects.filter(creator=self.request.user).count()
        if current_count >= 20:
            return Response(
                {"error": "每个创作者最多只能上传20个作品集"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 获取上传的文件列表（兼容新旧客户端）
        image_files = request.FILES.getlist('images')
        if not image_files and 'image' in request.FILES:
            image_files = [request.FILES['image']]

        if not image_files:
            return Response(
                {"error": "至少上传一张图片"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. 保存 Work 基本信息（不包含图片）
        work_serializer = self.get_serializer(data=request.data)
        work_serializer.is_valid(raise_exception=True)
        work = work_serializer.save(creator=self.request.user)

        # 4. 批量创建 WorkImage，并设置封面图
        for idx, img_file in enumerate(image_files):
            work_image = WorkImage.objects.create(
                work=work,
                image=img_file,
                order=idx
            )
            # 将第一张图设为封面
            if idx == 0:
                work.image = work_image.image
                work.save()

        # 5. 返回完整数据（包含 images 列表）
        headers = self.get_success_headers(work_serializer.data)
        return Response(
            self.get_serializer(work).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class WorkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """作品详情、更新、删除"""
    permission_classes = [IsCreator]  # 只有创作者可以访问
    serializer_class = WorkSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """只允许用户操作自己的作品"""
        return Work.objects.filter(creator=self.request.user)

    def perform_destroy(self, instance):
        """删除作品时，关联的 WorkImage 也会级联删除"""
        instance.delete()


class WorkImageViewSet(viewsets.ModelViewSet):
    """管理作品集中的图片（增删改查、排序）"""
    permission_classes = [IsCreator]
    serializer_class = WorkImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # 只返回当前创作者的作品图片
        return WorkImage.objects.filter(work__creator=self.request.user).order_by('order')

    def perform_create(self, serializer):
        # 确保图片属于当前创作者的作品
        work_id = self.request.data.get('work')
        work = get_object_or_404(Work, id=work_id, creator=self.request.user)
        # 自动分配顺序：当前最大 order + 1
        max_order = work.images.aggregate(models.Max('order'))['order__max'] or -1
        serializer.save(work=work, order=max_order + 1)
        # 如果是第一张图，更新 Work 封面
        if max_order == -1:
            work.image = serializer.instance.image
            work.save()

    def perform_update(self, serializer):
        # 更新图片信息，如果 order 变化可能需要调整其他图片的顺序，这里简化处理
        serializer.save()

    def perform_destroy(self, instance):
        work = instance.work
        instance.delete()
        # 如果删除的是封面图，将剩余的第一张图设为封面
        if work.image == instance.image:
            first_image = work.images.first()
            if first_image:
                work.image = first_image.image
            else:
                work.image = None
            work.save()


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
    """公开作品墙，支持按地点、标签、创作者筛选"""
    permission_classes = [permissions.AllowAny]
    serializer_class = WorkSerializer

    def get_queryset(self):
        queryset = Work.objects.filter(is_public=True).order_by('-created_at')
        
        location_id = self.request.query_params.get('location_id')
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        
        creator_id = self.request.query_params.get('creator_id')
        if creator_id:
            queryset = queryset.filter(creator_id=creator_id)
        
        tag = self.request.query_params.get('tag')
        if tag:
            # JSONField 包含查询（需数据库支持，否则用icontains备选）
            queryset = queryset.filter(tags__contains=[tag])
        
        return queryset


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


# ========== 新增：地图相关视图 ==========

class LocationMapView(generics.ListAPIView):
    """全校出片地图：返回所有活跃地点，包含作品数量和代表作品缩略图"""
    permission_classes = [permissions.AllowAny]
    serializer_class = LocationListSerializer

    def get_queryset(self):
        # 子查询：获取每个地点最新公开作品的图片URL
        latest_work_image = Work.objects.filter(
            location=OuterRef('pk'),
            is_public=True
        ).order_by('-created_at').values('image')[:1]

        queryset = Location.objects.filter(is_active=True).annotate(
            work_count=Count('work', filter=Q(work__is_public=True)),
            cover_image=Subquery(latest_work_image)
        ).order_by('name')
        return queryset


class MyLocationMapView(APIView):
    """我的出片地图：返回当前用户有作品的地点及个人作品缩略图"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # 获取用户有作品的地点ID
        location_ids = Work.objects.filter(
            creator=user, 
            is_public=True,
            location__isnull=False
        ).values_list('location', flat=True).distinct()
        
        # 获取地点对象
        locations = Location.objects.filter(id__in=location_ids, is_active=True)

        # 构建每个地点的用户作品预览（最多3张）
        result = []
        for loc in locations:
            works = Work.objects.filter(
                creator=user,
                location=loc,
                is_public=True
            ).order_by('-created_at')[:3]
            
            user_works = [
                {'id': w.id, 'image': w.image.url if w.image else None} 
                for w in works
            ]
            work_count = Work.objects.filter(
                creator=user, 
                location=loc, 
                is_public=True
            ).count()
            
            result.append({
                'id': loc.id,
                'name': loc.name,
                'longitude': float(loc.longitude),
                'latitude': float(loc.latitude),
                'work_count': work_count,
                'user_works': user_works
            })

        return Response(result)


class LocationWorksView(generics.ListAPIView):
    """地点详情页：返回指定地点的所有公开作品"""
    permission_classes = [permissions.AllowAny]
    serializer_class = WorkSerializer

    def get_queryset(self):
        location_id = self.kwargs.get('location_id')
        return Work.objects.filter(
            location_id=location_id,
            is_public=True
        ).order_by('-created_at')
    

# ========== 点赞 ==========
class WorkLikeToggleView(APIView):
    """点赞/取消点赞作品"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, work_id):
        work = get_object_or_404(Work, id=work_id)
        like, created = WorkLike.objects.get_or_create(user=request.user, work=work)
        if not created:
            like.delete()
            # 更新 like_count（可选，通过信号或手动更新）
            work.like_count = work.likes.count()
            work.save()
            return Response({"liked": False, "like_count": work.like_count})
        work.like_count = work.likes.count()
        work.save()
        return Response({"liked": True, "like_count": work.like_count})


# ========== 评论 ==========
class CommentListCreateView(generics.ListCreateAPIView):
    """评论列表和创建"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        work_id = self.kwargs.get('work_id')
        return Comment.objects.filter(work_id=work_id, is_deleted=False).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        work_id = self.kwargs.get('work_id')
        work = get_object_or_404(Work, id=work_id)
        serializer.save(user=self.request.user, work=work)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """评论详情、修改、删除"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user, is_deleted=False)
    
    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


# ========== 收藏 ==========
class FavoriteToggleView(APIView):
    """收藏/取消收藏作品"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, work_id):
        work = get_object_or_404(Work, id=work_id)
        favorite, created = Favorite.objects.get_or_create(user=request.user, work=work)
        if not created:
            favorite.delete()
            return Response({"favorited": False})
        return Response({"favorited": True})


class UserFavoriteListView(generics.ListAPIView):
    """用户收藏列表"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by('-created_at')


# ========== 新增：标签列表接口（用于前端选择） ==========
class TagListView(APIView):
    """
    获取所有预设标签，按分类组织返回。
    任何人都可以访问，用于发布需求、创作者编辑资料时的标签选择。
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tags_by_category = {
            'scene': [{'id': t[0], 'name': t[1]} for t in TAGS if t[2] == CATEGORY_SCENE],
            'skill': [{'id': t[0], 'name': t[1]} for t in TAGS if t[2] == CATEGORY_SKILL],
            'special': [{'id': t[0], 'name': t[1]} for t in TAGS if t[2] == CATEGORY_SPECIAL],
            'post': [{'id': t[0], 'name': t[1]} for t in TAGS if t[2] == CATEGORY_POST],
        }
        return Response(tags_by_category)