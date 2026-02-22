from django.db import models

# Create your models here.
from users.models import User


class GroupBuy(models.Model):
    """拼单信息"""

    STATUS_CHOICES = [
        ('recruiting', '招人中'),
        ('full', '已满员'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    # 发起者（拼单的创建者）
    initiator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='initiated_groupbuys',
        verbose_name='发起者'
    )

    # 拼单类型（如"樱花季团拍"）
    title = models.CharField('拼单标题', max_length=100)
    description = models.TextField('拼单描述')

    # 人数和费用
    target_people_count = models.IntegerField('目标人数', default=2)  # 如 3 人团
    cost_per_person = models.DecimalField('每人费用(元)', max_digits=8, decimal_places=2)

    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='recruiting')

    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'groupbuy'
        verbose_name = '拼单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.initiator.username})"

    def get_current_members_count(self):
        """获取当前已加入人数（包括发起者）"""
        # 返回成员数 + 1（发起者也算一个人）
        return self.members.count() + 1

    def is_full(self):
        """判断是否已满员"""
        return self.get_current_members_count() >= self.target_people_count


class GroupBuyMember(models.Model):
    """拼单成员（多对多关系表）"""

    groupbuy = models.ForeignKey(
        GroupBuy,
        on_delete=models.CASCADE,
        related_name='members',  # 可以通过 groupbuy.members.all() 查成员
        verbose_name='所属拼单'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='joined_groupbuys',  # 可以通过 user.joined_groupbuys.all() 查加入的拼单
        verbose_name='用户'
    )

    # 加入时间
    joined_at = models.DateTimeField('加入时间', auto_now_add=True)

    class Meta:
        db_table = 'groupbuy_member'
        verbose_name = '拼单成员'
        verbose_name_plural = verbose_name
        # 防止重复加入同一拼单
        unique_together = [['groupbuy', 'user']]
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.groupbuy.title}"