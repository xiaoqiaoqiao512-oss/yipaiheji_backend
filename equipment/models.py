from django.db import models
from users.models import User
# Create your models here.


class Equipment(models.Model):
    """设备租赁模块"""

    POST_TYPE_CHOICES = [
        ('rent', '出租'),
        ('lease', '求租'),
    ]

    CATEGORY_CHOICES = [
        ('camera', '摄影器材'),
        ('lens','镜头'),
        ('drone','无人机'),
        ('other','其他'),
    ]

    STATUS_CHOICES = [
        ('active', '进行中'),
        ('closed','已关闭'),
    ]

    publisher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='equipment_posts',
        verbose_name='发布者'
    )
    post_type = models.CharField('信息类型',max_length=20,choices=POST_TYPE_CHOICES)
    category = models.CharField('设备类别',max_length=20,choices=CATEGORY_CHOICES)
    device_model = models.CharField('设备型号',max_length=100)
    rent_per_day = models.DecimalField('日租金',max_digits=10,decimal_places=2)
    deposit = models.DecimalField('押金', max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField('描述',blank=True)
    status = models.CharField('状态',max_length=20,choices=STATUS_CHOICES,default='active')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'equipment'
        verbose_name = '设备信息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post_type','status','created_at']),
            models.Index(fields=['category','created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_post_type_display()}-{self.device_model} ({self.publisher.username})"


class EquipmentImage(models.Model):
    """设备图片（最多 3 张，由序列化器校验）"""

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='设备信息'
    )
    image = models.ImageField('设备图片', upload_to='equipment/')
    created_at = models.DateTimeField('上传时间', auto_now_add=True)

    class Meta:
        db_table = 'equipment_images'
        verbose_name = '设备图片'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return f"{self.equipment.device_model}-image-{self.id}"