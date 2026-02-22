from django.db import models
from users.models import User


class Message(models.Model):
    """邮件式聊天消息（支持私聊和群聊）"""

    MESSAGE_TYPE_CHOICES = [
        ('private', '私聊'),
        ('groupbuy', '拼单群聊'),
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='发送者'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # 群聊时为空
        related_name='received_messages',
        verbose_name='接收者（私聊用）'
    )

    # 消息类型：区分私聊和群聊
    message_type = models.CharField(
        '消息类型',
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='private'
    )

    # 群聊时关联的拼单（私聊时为空）
    # 需要延迟导入避免循环依赖
    groupbuy = models.ForeignKey(
        'groupbuy.GroupBuy',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_messages',  # groupbuy.chat_messages.all() 查群聊
        verbose_name='关联拼单（群聊用）'
    )

    content = models.TextField('消息内容')
    is_read = models.BooleanField('是否已读', default=False)

    created_at = models.DateTimeField('发送时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'chat_messages'
        verbose_name = '聊天消息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['message_type', 'groupbuy']),  # 优化群聊查询
        ]

    def __str__(self):
        if self.message_type == 'private':
            return f"{self.sender.username} → {self.receiver.username}: {self.content[:50]}"
        else:
            return f"{self.sender.username} in {self.groupbuy.title}: {self.content[:50]}"

    def mark_as_read(self):
        """标记消息为已读"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])