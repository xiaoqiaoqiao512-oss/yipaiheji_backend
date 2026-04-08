# users/views.py
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import ListAPIView

from .serializers import (
    UserRegisterSerializer, UserProfileSerializer, StudentCardUploadSerializer,
    CreatorApplySerializer
)
from .models import User, CreatorSampleImage

# ---------- 响应序列化器定义 ----------
class RegisterResponseSerializer(serializers.Serializer):
    """注册响应格式"""
    message = serializers.CharField()
    user = inline_serializer(name='UserInfo', fields={
        'id': serializers.IntegerField(),
        'username': serializers.CharField(),
        'student_id': serializers.CharField(allow_null=True),
        'role': serializers.CharField(),
    })
    tokens = inline_serializer(name='Tokens', fields={
        'access': serializers.CharField(),
        'refresh': serializers.CharField(),
    })

class LoginResponseSerializer(serializers.Serializer):
    """登录响应格式"""
    message = serializers.CharField()
    user = UserProfileSerializer()  # 复用已有的用户信息序列化器
    tokens = inline_serializer(name='LoginTokens', fields={
        'access': serializers.CharField(),
        'refresh': serializers.CharField(),
    })

class ApplyCreatorResponseSerializer(serializers.Serializer):
    """申请创作者响应格式"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    user = UserProfileSerializer()

class CanApplyResponseSerializer(serializers.Serializer):
    """检查是否可以申请创作者的响应格式"""
    can_apply = serializers.BooleanField()
    reason = serializers.CharField()

# ---------- 原有视图 ----------
class RegisterView(APIView):
    """用户注册视图"""
    permission_classes = [AllowAny]  # 允许任何人访问

    @extend_schema(
        summary="用户注册",
        description="注册新用户，返回用户基本信息和JWT令牌",
        request=UserRegisterSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: OpenApiResponse(description="注册失败（如用户名已存在、数据验证错误）"),
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # 生成JWT Token
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "注册成功",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "student_id": user.student_id,
                    "role": user.role
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [AllowAny]

    @extend_schema(
        summary="用户登录",
        description="使用用户名和密码登录，返回JWT令牌和用户信息",
        request=inline_serializer(
            name='LoginRequest',
            fields={
                'username': serializers.CharField(help_text='用户名'),
                'password': serializers.CharField(help_text='密码', write_only=True),
            }
        ),
        responses={
            200: LoginResponseSerializer,
            400: OpenApiResponse(description="用户名或密码错误"),
        }
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # 验证用户名和密码
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(password):
            return Response({"error": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成JWT Token
        refresh = RefreshToken.for_user(user)
        
        # 使用UserProfileSerializer返回完整用户信息
        serializer = UserProfileSerializer(user, context={'request': request})
        
        return Response({
            "message": "登录成功",
            "user": serializer.data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })


class UserProfileView(APIView):
    """获取当前用户信息"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="获取当前用户资料",
        description="需要认证，返回当前登录用户的详细信息",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="未认证或token无效"),
        }
    )
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)


class UploadStudentCardView(APIView):
    """上传学生卡照片（用于校园认证）"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 支持文件上传

    @extend_schema(
        summary="上传学生卡照片",
        description="用于校园认证，上传学生卡照片（图片文件）",
        request=StudentCardUploadSerializer,
        responses={200: UserProfileSerializer, 400: "上传失败"}
    )
    def post(self, request):
        user = request.user
        serializer = StudentCardUploadSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # 返回更新后的完整用户信息
            profile_serializer = UserProfileSerializer(user, context={'request': request})
            return Response(profile_serializer.data, status=200)
        return Response(serializer.errors, status=400)


class ApplyCreatorView(APIView):
    """用户申请成为创作者（需上传2-5张样片）"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="申请成为创作者",
        description="上传2-5张样片作品，提交申请（需要已通过校园认证）",
        request=CreatorApplySerializer,
        responses={
            200: ApplyCreatorResponseSerializer,
            400: OpenApiResponse(description="申请失败（如样片数量不对、未认证等）"),
        }
    )
    def post(self, request):
        user = request.user

        # 1. 验证样片
        apply_serializer = CreatorApplySerializer(data=request.data)
        if not apply_serializer.is_valid():
            return Response(apply_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sample_images = apply_serializer.validated_data['sample_images']

        # 2. 检查申请条件（复用原有逻辑）
        if not user.can_apply_as_creator():
            return Response({
                "success": False,
                "error": "无法申请创作者，请先完成校园认证或您已经是创作者"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. 检查是否已有 pending 申请（避免重复提交）
        if user.creator_application_status == 'pending':
            return Response({
                "success": False,
                "error": "您已经提交过申请，请等待审核"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 4. 删除该用户之前的所有样片（重新申请时覆盖旧数据）
        user.sample_images.all().delete()

        # 5. 保存新的样片
        for img in sample_images:
            CreatorSampleImage.objects.create(user=user, image=img)

        # 6. 调用原有申请方法（将状态改为 pending）
        success, message = user.apply_as_creator()

        if success:
            # 返回更新后的用户信息（包含样片 URL）
            serializer = UserProfileSerializer(user, context={'request': request})
            return Response({
                "success": True,
                "message": message,
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            # 如果失败（理论上不会，因为前面检查过），清理已保存的样片
            user.sample_images.all().delete()
            return Response({
                "success": False,
                "error": message
            }, status=status.HTTP_400_BAD_REQUEST)


class CanApplyCreatorView(APIView):
    """检查当前用户是否可以申请成为创作者"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="检查是否可申请创作者",
        description="返回当前用户是否可以申请成为创作者（如是否已认证、是否已申请）",
        responses={
            200: CanApplyResponseSerializer,
        }
    )
    def get(self, request):
        user = request.user
        can_apply = user.can_apply_as_creator()
        
        # 额外检查：如果已有 pending 申请，也不能再次申请
        if user.creator_application_status == 'pending':
            can_apply = False
            reason = "您已经提交过申请，请等待审核"
        else:
            reason = "可以申请成为创作者" if can_apply else "无法申请，请先完成校园认证或您已经是创作者"
        
        return Response({
            "can_apply": can_apply,
            "reason": reason
        })


# ---------- 管理员视图 ----------
class PendingCreatorApplicationsView(ListAPIView):
    """管理员：查看所有待审核的创作者申请（含样片）"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        return User.objects.filter(creator_application_status='pending')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class ReviewCreatorApplicationView(APIView):
    """管理员：审核创作者申请（通过/拒绝）"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="审核创作者申请",
        description="通过或拒绝用户的创作者申请，需要传入 action=approve 或 reject",
        request=inline_serializer(
            name='ReviewRequest',
            fields={
                'action': serializers.ChoiceField(choices=['approve', 'reject']),
            }
        ),
        responses={200: UserProfileSerializer}
    )
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)

        if user.creator_application_status != 'pending':
            return Response({"error": "该用户没有待审核的创作者申请"}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action')
        if action == 'approve':
            success, message = user.approve_creator_application()
        elif action == 'reject':
            success, message = user.reject_creator_application()
        else:
            return Response({"error": "action 必须是 approve 或 reject"}, status=status.HTTP_400_BAD_REQUEST)

        if success:
            # 审核通过后，样片可以保留作为作品集（或者根据业务需求决定是否删除）
            # 这里保留样片，以便前端展示
            serializer = UserProfileSerializer(user, context={'request': request})
            return Response(serializer.data)
        else:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)