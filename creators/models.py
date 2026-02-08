
from django.db import models
from users.models import User  # 导入我们自定义的User

class CreatorProfile(models.Model):
    """创作者详细信息档案"""
    
    # 关联到用户表，一对一关系
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # 用户删除时，档案也删除
        related_name='creator_profile',  # 反向查询名称
        verbose_name='关联用户'
    )
    
    # 服务信息
    service_intro = models.TextField('服务介绍', blank=True, null=True)
    base_price = models.DecimalField('基础价格', max_digits=8, decimal_places=2, default=0)
    price_range = models.CharField('价格区间', max_length=50, blank=True, null=True)  # 如 "100-300元"
    is_negotiable = models.BooleanField('接受议价', default=True)
    
    # 设备信息
    camera_model = models.CharField('相机型号', max_length=100, blank=True, null=True)
    can_provide_makeup = models.BooleanField('可提供化妆', default=False)
    can_provide_costume = models.BooleanField('可提供服装', default=False)
    
    # 统计信息
    completed_orders = models.IntegerField('完成订单数', default=0)
    average_rating = models.FloatField('平均评分', default=0.0)
    view_count = models.IntegerField('被查看次数', default=0)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'creator_profiles'  # 数据库表名
        verbose_name = '创作者档案'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.user.username}的创作者档案"


class Work(models.Model):
    """创作者的作品集"""
    
    # 关联到创作者
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,  # 创作者删除时，作品也删除
        related_name='works',  # 通过user.works可以查询所有作品
        verbose_name='创作者'
    )
    
    # 作品信息
    title = models.CharField('作品标题', max_length=100, blank=True, null=True)
    image = models.ImageField('作品图片', upload_to='works/')  # 必须上传
    description = models.TextField('作品描述', blank=True, null=True)
    
    # 标签系统
    tags = models.JSONField('标签', default=list, blank=True)  # 存储标签列表
    
    # 作品信息
    shooting_time = models.DateTimeField('拍摄时间', blank=True, null=True)
    shooting_location = models.CharField('拍摄地点', max_length=200, blank=True, null=True)
    
    # 互动数据
    like_count = models.IntegerField('点赞数', default=0)
    view_count = models.IntegerField('浏览数', default=0)
    
    # 状态
    is_public = models.BooleanField('是否公开', default=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'works'  # 数据库表名
        verbose_name = '作品'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']  # 默认按创建时间倒序排列
    
    def __str__(self):
        return f"{self.creator.username}的作品: {self.title or '未命名'}"