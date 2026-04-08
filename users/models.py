from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """自定义用户模型，扩展Django内置用户"""
    
    # 用户角色选择
    ROLE_CHOICES = [
        ('student', '普通学生'),
        ('creator', '创作者'),
        ('admin', '管理员'),
    ]
    
    # ========== 基础信息 ==========
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField('学号', max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField('手机号', max_length=15, blank=True, null=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    
    # ========== 认证状态 ==========
    # 是否完成校园认证（学生证/学号验证）
    is_verified = models.BooleanField('是否已认证', default=False)
    
    # 学生卡照片（用于认证）
    student_card_img = models.ImageField('学生卡照片', upload_to='student_cards/', blank=True, null=True)
    
    # 创作者申请状态
    creator_application_status = models.CharField(
        '创作者申请状态', 
        max_length=20,
        choices=[
            ('not_applied', '未申请'),
            ('pending', '审核中'),
            ('approved', '已通过'),
            ('rejected', '已拒绝'),
        ],
        default='not_applied'
    )
    
    # 创作者申请时间
    creator_applied_at = models.DateTimeField('创作者申请时间', blank=True, null=True)
    
    # ========== 个人简介 ==========
    bio = models.TextField('个人简介', blank=True, null=True)
    
    # ========== 标签 ==========
    tags = models.JSONField('标签', default=list, blank=True)  # 存储标签列表，如["人像", "夜景"]
    
    # ========== 统计信息（为后续功能预留） ==========
    completed_orders = models.IntegerField('完成订单数', default=0)
    
    # ========== 状态 ==========
    is_active_creator = models.BooleanField('是否活跃创作者', default=True)  # 创作者是否接单中
    
    # ========== 时间戳 ==========
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'users'  # 数据库表名
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.student_id or '未认证'})"
    
    @property
    def is_creator(self):
        """是否是创作者（已通过申请）"""
        return self.role == 'creator' and self.creator_application_status == 'approved'
    
    @property
    def display_role(self):
        """显示用户角色"""
        if self.is_creator:
            return "创作者"
        elif self.role == 'admin':
            return "管理员"
        else:
            return "学生"
    
    def can_apply_as_creator(self):
        """检查是否可以申请成为创作者"""
        # 可以申请的条件：
        # 1. 已完成校园认证
        # 2. 当前不是创作者
        return self.is_verified and not self.is_creator
    
    def apply_as_creator(self):
        """用户申请成为创作者"""
        if not self.is_verified:
            return False, "请先完成校园认证"
        
        if self.is_creator:
            return False, "您已经是创作者了"
        
        # 无论之前状态如何（包括被拒绝），都可以重新申请
        self.creator_application_status = 'pending'
        self.creator_applied_at = timezone.now()
        self.save()
        return True, "创作者申请已提交，请等待审核"
    
    def approve_creator_application(self):
        """管理员通过创作者申请"""
        if self.creator_application_status != 'pending':
            return False, "没有待处理的创作者申请"
        
        # 批准申请
        self.role = 'creator'
        self.creator_application_status = 'approved'
        self.save()
        
        # 导入在方法内部，避免循环导入
        try:
            from creators.models import CreatorProfile
            # 自动创建创作者档案（如果不存在）
            if not hasattr(self, 'creator_profile'):
                CreatorProfile.objects.create(user=self)
        except ImportError:
            # 如果creators应用还没准备好，跳过创建CreatorProfile
            pass
        
        return True, "创作者申请已通过"
    
    def reject_creator_application(self):
        """管理员拒绝创作者申请"""
        if self.creator_application_status != 'pending':
            return False, "没有待处理的创作者申请"
        
        # 拒绝申请
        self.creator_application_status = 'rejected'
        self.save()
        
        # 删除关联的创作者档案（如果存在）
        try:
            if hasattr(self, 'creator_profile'):
                self.creator_profile.delete()
        except Exception:
            # 如果删除失败，继续执行（可能是已经不存在了）
            pass
        
        return True, "创作者申请已被拒绝"


class CreatorSampleImage(models.Model):
    """创作者申请时上传的样片（作品示例），每张图片一条记录"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sample_images',
        verbose_name='申请用户'
    )
    image = models.ImageField('样片图片', upload_to='creator_samples/')
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)

    class Meta:
        db_table = 'creator_sample_images'
        verbose_name = '创作者样片'
        verbose_name_plural = verbose_name
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.user.username} 的样片 {self.id}"