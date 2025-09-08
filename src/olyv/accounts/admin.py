from django.contrib import admin
from django.contrib.auth.admin import (
    GroupAdmin as AbstractGroupAdmin,
)
from django.contrib.auth.admin import (
    UserAdmin as AbstractUserAdmin,
)
from django.utils.html import format_html

from olyv.base.adminsite import admin_site

from .forms import UserForm
from .models import Group, GroupDescription, User


@admin.register(Group, site=admin_site)
class GroupAdmin(AbstractGroupAdmin):
    pass


@admin.register(GroupDescription, site=admin_site)
class GroupDescriptionAdmin(admin.ModelAdmin):
    readonly_fields = ("description", "permissions_table")

    def permissions_table(self, obj):
        """Display permissions in a table format"""
        if not obj or not obj.group:
            return "No permissions"

        permissions = obj.group.permissions.select_related("content_type").order_by(
            "content_type__app_label", "codename"
        )
        if not permissions:
            return "No permissions"

        html = '<table style="width:100%; border-collapse: collapse;"><tr style="background:#f2f2f2;"><th style="border:1px solid #ddd;padding:8px;">App.Model</th><th style="border:1px solid #ddd;padding:8px;">Permission</th></tr>'
        for perm in permissions:
            html += f'<tr><td style="border:1px solid #ddd;padding:8px;">{perm.content_type.app_label}.{perm.content_type.model}</td><td style="border:1px solid #ddd;padding:8px;">{perm.codename}</td></tr>'
        html += "</table>"

        return format_html(html)

    permissions_table.short_description = "Permissions"

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets = list(fieldsets)
        for name, section in fieldsets:
            if "fields" in section:
                section["fields"] = tuple(field for field in section["fields"] if field != "group")
        return fieldsets


@admin.register(User, site=admin_site)
class UserAdmin(AbstractUserAdmin):
    readonly_fields = ("is_staff", "is_superuser", "date_joined", "last_login")
    form = UserForm

    def get_form(self, request, obj=None, **kwargs):
        """Override get_form to pass the current user to the form"""
        Form = super().get_form(request, obj, **kwargs)
        return lambda *args, **k: Form(*args, **{**k, "current_user": request.user})

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        if request.user.is_superuser:
            return fieldsets

        # Hide sensitive fields for all non-superusers
        fieldsets = list(fieldsets)
        restricted_fields = ["is_staff", "is_superuser", "user_permissions"]

        # Add more restricted fields for users not in ACCOUNTS_MANAGER group
        is_accounts_manager = request.user.groups.filter(name="ACCOUNTS_MANAGER").exists()
        if not is_accounts_manager:
            restricted_fields.extend(["password", "last_login", "date_joined", "groups"])

        # Filter fieldsets and remove empty ones
        filtered_fieldsets = []
        for name, section in fieldsets:
            if name == "Important dates" and not is_accounts_manager:
                continue

            if "fields" in section:
                new_fields = tuple(
                    field for field in section["fields"] if field not in restricted_fields
                )
                if new_fields:  # Only add section if it has fields
                    section["fields"] = new_fields
                    filtered_fieldsets.append((name, section))
            else:
                filtered_fieldsets.append((name, section))

        return filtered_fieldsets
