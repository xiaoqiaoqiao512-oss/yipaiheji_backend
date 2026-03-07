from django.db import models
from users.models import User 

class CreatorProfile(models.Model):
    """创作者详细信息档案"""
    
    # 关联到用户表，一对一关系
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # 用户删除时，档案也删除
        related_name='creator_profile',  # 反向查询名称
        verbose_name='关联用户'
    )
    
    # 存储标签ID列表
    tags = models.JSONField('创作者标签', default=list, blank=True)  
    
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
    
class Location(models.Model):
    """武大出片地图预设地点"""
    CATEGORY_CHOICES = [
        ('landmark', '地标打卡型'),
        ('nature', '自然景观型'),
        ('life', '校园生活型'),
        ('architecture', '典型建筑型'),
    ]
    CAMPUS_CHOICES = [
        ('wl', '文理学部'),
        ('gc', '工学部'),
        ('xx', '信息学部'),
        ('yx', '医学部'),
        ('other', '其他'),
    ]

    name = models.CharField('地点名称', max_length=100, unique=True)
    longitude = models.DecimalField('经度', max_digits=9, decimal_places=6)
    latitude = models.DecimalField('纬度', max_digits=9, decimal_places=6)
    description = models.TextField('简短描述', blank=True, null=True)
    category = models.CharField('分类', max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    campus = models.CharField('学部', max_length=20, choices=CAMPUS_CHOICES, blank=True, null=True)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        db_table = 'locations'
        verbose_name = '拍摄地点'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return self.name


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
    # 修改 image 字段为可选（封面图），并添加帮助文本
    image = models.ImageField(
        '封面图片',
        upload_to='works/',
        blank=True,
        null=True,
        help_text='自动从上传图片的第一张生成'
    )
    description = models.TextField('作品描述', blank=True, null=True)
    
    # 标签系统
    tags = models.JSONField('标签', default=list, blank=True)  # 存储标签列表
    
    # 作品信息
    shooting_time = models.DateTimeField('拍摄时间', blank=True, null=True)
    shooting_location = models.CharField('拍摄地点', max_length=200, blank=True, null=True)
    # 新增：关联预设地点库
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='关联地点'
    )
    
    # 互动数据
    like_count = models.IntegerField('点赞数', default=0)
    view_count = models.IntegerField('浏览数', default=0)
    
    # 状态
    is_public = models.BooleanField('是否公开', default=True)
    
    # 新增：作品集排序（用于拖拽排序）
    display_order = models.IntegerField('排序', default=0)
    
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
    

class WorkImage(models.Model):
    """作品集中的单张图片"""
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='所属作品集'
    )
    image = models.ImageField('图片文件', upload_to='works/')
    order = models.PositiveIntegerField('排序', default=0)
    created_at = models.DateTimeField('上传时间', auto_now_add=True)

    class Meta:
        db_table = 'work_images'
        ordering = ['order']
        unique_together = ('work', 'order')  # 同一作品集内顺序不重复
        verbose_name = '作品图片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.work.title} 的第 {self.order} 张图'


class WorkLike(models.Model):
    """作品点赞记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_likes')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'work_likes'
        unique_together = ('user', 'work')  # 防止重复点赞
        verbose_name = '作品点赞'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 点赞了 {self.work.title}"


class Comment(models.Model):
    """作品评论"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField('评论内容')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # 软删除

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']
        verbose_name = '评论'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 评论了 {self.work.title}"


class Favorite(models.Model):
    """用户收藏作品"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites'
        unique_together = ('user', 'work')
        verbose_name = '收藏'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 收藏了 {self.work.title}"
    

class Service(models.Model):
    """创作者的服务项目"""
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='创作者'
    )
    
    # 服务基本信息
    name = models.CharField('服务名称', max_length=100)
    description = models.TextField('服务描述')
    base_price = models.DecimalField('基础价格', max_digits=8, decimal_places=2)
    price_range = models.CharField('价格区间', max_length=50, blank=True, null=True)  # 如 "100-300元"
    estimated_time = models.CharField('预计时长', max_length=50, blank=True, null=True)  # 如 "2小时"
    
    # 服务配置
    is_negotiable = models.BooleanField('接受议价', default=True)
    is_available = models.BooleanField('可接单', default=True)
    
    # 标签
    tags = models.JSONField('标签', default=list, blank=True)
    
    # 统计数据
    order_count = models.IntegerField('接单次数', default=0)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'services'
        verbose_name = '服务项目'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.creator.username}的服务：{self.name}"