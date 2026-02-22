from django.db import models
from users.models import User

class Demand(models.Model):
    """用户发布的需求"""
    
    # 需求状态
    STATUS_CHOICES = [
        ('pending', '待接单'),
        ('matched', '已接单'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    # 需求类型
    TYPE_CHOICES = [
        ('photo', '约拍'),
        ('makeup', '妆造'),
        ('retouch', '修图'),
    ]
    
    # 发布者信息
    publisher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='published_demands',
        verbose_name='发布者'
    )
    
    # 基础信息
    title = models.CharField('需求标题', max_length=100)
    demand_type = models.CharField('需求类型', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('详细描述')
    
    # 时间地点
    shooting_time = models.DateTimeField('拍摄时间')
    location = models.CharField('拍摄地点', max_length=200)
    campus_location = models.CharField('校内地点', max_length=100, blank=True, null=True)  # 如"樱顶老图"
    
    # 预算和人数
    budget = models.DecimalField('预算', max_digits=8, decimal_places=2)
    min_budget = models.DecimalField('最低预算', max_digits=8, decimal_places=2, blank=True, null=True)
    max_budget = models.DecimalField('最高预算', max_digits=8, decimal_places=2, blank=True, null=True)
    people_count = models.IntegerField('人数', default=1)
    
    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 标签和专题
    tags = models.JSONField('标签', default=list, blank=True)  # 如["毕业照", "夜景"]
    special_topic = models.CharField('特色专题', max_length=50, blank=True, null=True)  # 如"樱花季"
    
    # 参考图片（存储JSON，包含图片路径列表）
    reference_images = models.JSONField('参考图', default=list, blank=True)
    
    # 匹配的创作者（如果有）
    matched_creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='matched_demands',
        null=True, blank=True,
        verbose_name='匹配的创作者'
    )
    
    # 统计信息
    view_count = models.IntegerField('浏览数', default=0)
    comment_count = models.IntegerField('评论数', default=0)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'demands'
        verbose_name = '需求'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['demand_type', 'created_at']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.publisher.username}的需求：{self.title}"


class DemandComment(models.Model):
    """需求评论（创作者报价）"""
    
    # 评论状态
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    ]
    
    # 关联关系
    demand = models.ForeignKey(
        Demand,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='关联需求'
    )
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='demand_comments',
        verbose_name='创作者'
    )
    
    # 报价信息
    bid_price = models.DecimalField('报价', max_digits=8, decimal_places=2)
    message = models.TextField('留言')
    
    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'demand_comments'
        verbose_name = '需求评论'
        verbose_name_plural = verbose_name
        ordering = ['created_at']
        unique_together = ['demand', 'creator']  # 一个创作者对一个需求只能报价一次
    
    def __str__(self):
        return f"{self.creator.username}对{self.demand.title}的报价"
