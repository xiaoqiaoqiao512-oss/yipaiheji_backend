"""
URL configuration for yipaiheji project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# yipaiheji/urls.py 

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 用户相关API
    path('api/users/', include('users.urls')),
    
    # 创作者相关API
    path('api/creators/', include('creators.urls')),  

    path('api/demands/', include('demands.urls')), 

    # 聊天API
    path('api/chat/', include('chat.urls')),
    
    # 设备租赁
    path('api/equipment/', include('equipment.urls')),
    
    # 拼单社区
    path('api/groupbuy/', include('groupbuy.urls')),
    
    # JWT Token刷新
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
