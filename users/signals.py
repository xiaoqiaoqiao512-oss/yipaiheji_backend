# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from creators.models import CreatorProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """用户创建时自动创建对应的创作者档案（如果是创作者）"""
    if created and instance.role == 'creator':
        CreatorProfile.objects.create(user=instance)