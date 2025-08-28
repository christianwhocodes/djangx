from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as ProxiedGroup
from django.db import models

from olyv.base.models import AbstractDisplayOrder


class Group(ProxiedGroup):
    """
    Custom Group model that extends the default Django Group.
    This allows for additional fields or methods in the future if needed.
    """

    class Meta:
        proxy = True

    def __str__(self):
        return self.name


class GroupDescription(models.Model):
    """Model to store group descriptions for admin display"""

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="description")
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "auth_group_description"
        verbose_name = "Group Description"
        verbose_name_plural = "Group Descriptions"
        ordering = ["group__name"]

    def __str__(self):
        return self.group.name

    # @property
    # def permissions(self):
    #     """Return a list of permission names for this group."""
    #     return [perm.name for perm in self.group.permissions.all()]


class User(AbstractUser, AbstractDisplayOrder):
    """Custom User model with group-based permissions and staff status management"""

    email = models.EmailField(blank=True, null=True)
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "auth_user"
        ordering = ["display_order", "username"]

    def update_staff_status(self):
        """Update is_staff based on group membership in signals.py"""
        self.is_staff = self.groups.exists()
        # Use update() to avoid triggering save() again
        User.objects.filter(pk=self.pk).update(is_staff=self.is_staff)
