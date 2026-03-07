from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Work, WorkLike

@receiver(post_save, sender=WorkLike)
def increment_like_count(sender, instance, created, **kwargs):
    if created:
        work = instance.work
        work.like_count = work.likes.count()
        work.save(update_fields=['like_count'])

@receiver(post_delete, sender=WorkLike)
def decrement_like_count(sender, instance, **kwargs):
    work = instance.work
    work.like_count = work.likes.count()
    work.save(update_fields=['like_count'])