from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import User


@receiver(m2m_changed, sender=User.groups.through)
def update_user_staff_status(sender, instance, action, **kwargs):
    if action in ["post_add"]:
        instance.update_staff_status()
    elif action in ["post_remove", "post_clear"]:
        # Reload the user from the database to get the latest group membership
        user = User.objects.get(pk=instance.pk)
        user.update_staff_status()
