# users/views.py
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import UserRegisterSerializer, UserProfileSerializer ,StudentCardUploadSerializer
from .models import User

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

class UploadStudentCardView(APIView):
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
            profile_serializer = UserProfileSerializer(user)
            return Response(profile_serializer.data, status=200)
        return Response(serializer.errors, status=400)
    
class ApplyCreatorResponseSerializer(serializers.Serializer):
    """申请创作者响应格式"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    user = UserProfileSerializer()

class CanApplyResponseSerializer(serializers.Serializer):
    """检查是否可以申请创作者的响应格式"""
    can_apply = serializers.BooleanField()
    reason = serializers.CharField()

# ---------- 视图 ----------
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
        serializer = UserProfileSerializer(user)
        
        return Response({
            "message": "登录成功",
            "user": serializer.data,  # 使用序列化器的数据
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
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class ApplyCreatorView(APIView):
    """用户申请成为创作者"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="申请成为创作者",
        description="当前用户申请成为创作者（需要认证）",
        request=None,  # 假设该接口不需要请求体
        responses={
            200: ApplyCreatorResponseSerializer,
            400: OpenApiResponse(description="申请失败（如已申请或不符合条件）"),
        }
    )
    def post(self, request):
        user = request.user
        
        # 调用User模型的方法
        success, message = user.apply_as_creator()
        
        if success:
            # 返回更新后的用户信息
            serializer = UserProfileSerializer(user)
            return Response({
                "success": True,
                "message": message,
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        else:
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
        
        return Response({
            "can_apply": can_apply,
            "reason": "可以申请成为创作者" if can_apply else "无法申请，请先完成校园认证或您已经是创作者"
        })