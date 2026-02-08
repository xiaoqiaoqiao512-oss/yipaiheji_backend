from django.contrib import admin
from .models import CreatorProfile, Work

# 注册创作者档案和作品模型
admin.site.register(CreatorProfile)
admin.site.register(Work)
