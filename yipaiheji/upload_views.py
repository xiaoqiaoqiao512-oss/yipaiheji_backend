import os
import re
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class GlobalSingleImageUploadView(APIView):
    """全局单图上传接口，支持各业务模块复用。"""

    permission_classes = [permissions.IsAuthenticated]
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_TYPES = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/webp': '.webp',
    }
    BIZ_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,30}$')

    @classmethod
    def _normalize_biz(cls, biz):
        if not biz:
            return 'common'

        text = str(biz).strip().lower()
        if cls.BIZ_PATTERN.match(text):
            return text
        return 'common'

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': '图片文件（JPEG/PNG/WEBP，最大5MB）'
                    },
                    'biz': {
                        'type': 'string',
                        'description': '业务标识，如 demands、equipment、works，默认 common'
                    }
                },
                'required': ['image']
            }
        },
        responses={
            201: OpenApiResponse(
                description='上传成功',
                response={
                    'type': 'object',
                    'properties': {
                        'url': {'type': 'string'},
                        'path': {'type': 'string'},
                        'biz': {'type': 'string'},
                    }
                }
            ),
            400: OpenApiResponse(description='请求错误（缺少文件、大小超限、格式不支持）'),
            401: OpenApiResponse(description='未认证'),
        },
        description='全局单图上传接口。前端可多次调用上传多张图，每次仅传一张 image。'
    )
    def post(self, request):
        file = request.FILES.get('image')
        if not file:
            return Response(
                {'error': "请上传图片，字段名为 'image'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.size > self.MAX_SIZE:
            return Response(
                {'error': f"图片大小不能超过 {self.MAX_SIZE // (1024 * 1024)}MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.content_type not in self.ALLOWED_TYPES:
            return Response(
                {'error': '仅支持 JPEG/PNG/WEBP 格式'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        biz = self._normalize_biz(request.data.get('biz'))

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in {'.jpg', '.jpeg', '.png', '.webp'}:
            ext = self.ALLOWED_TYPES[file.content_type]

        filename = f'{uuid.uuid4().hex}{ext}'
        sub_path = f'uploads/{biz}/user_{request.user.id}/'
        full_path = default_storage.save(sub_path + filename, ContentFile(file.read()))
        url = request.build_absolute_uri(settings.MEDIA_URL + full_path)

        return Response(
            {
                'url': url,
                'path': full_path,
                'biz': biz,
            },
            status=status.HTTP_201_CREATED,
        )
