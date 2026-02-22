from django.shortcuts import render
# users/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegisterSerializer, UserProfileSerializer
from .models import User

class RegisterView(APIView):
    """用户注册视图"""
    permission_classes = [AllowAny]  # 允许任何人访问
    
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
        
        #  使用UserProfileSerializer返回完整用户信息
        serializer = UserProfileSerializer(user)
        
        return Response({
            "message": "登录成功",
            "user": serializer.data,  #  使用序列化器的数据
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })


class UserProfileView(APIView):
    """获取当前用户信息"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


#  新增：申请成为创作者视图
class ApplyCreatorView(APIView):
    """用户申请成为创作者"""
    permission_classes = [IsAuthenticated]
    
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


#  新增：检查是否可以申请成为创作者
class CanApplyCreatorView(APIView):
    """检查当前用户是否可以申请成为创作者"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        can_apply = user.can_apply_as_creator()
        
        return Response({
            "can_apply": can_apply,
            "reason": "可以申请成为创作者" if can_apply else "无法申请，请先完成校园认证或您已经是创作者"
        })