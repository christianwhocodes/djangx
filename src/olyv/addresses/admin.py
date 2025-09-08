from django.contrib import admin

from olyv.base.adminsite import admin_site

from .forms import SocialMediaAddressForm
from .models import (
    EmailAddress,
    PhoneAddress,
    PhysicalAddress,
    SocialMediaAddress,
)


@admin.register(SocialMediaAddress, site=admin_site)
class SocialMediaAddressAdmin(admin.ModelAdmin):
    """
    Admin interface for ContactSocialLink model, supporting listing, filtering, searching,
    and inline editing of URLs and order. Restricts the 'name' field to read-only on edit.
    """

    form = SocialMediaAddressForm
    list_display = ("name", "url", "is_active", "display_order")
    list_editable = ("url", "display_order")
    list_filter = ("is_active",)
    search_fields = ("name", "url")
    fieldsets = (
        (
            "Social Media Details",
            {
                "fields": (
                    "name",
                    "url",
                )
            },
        ),
        ("Display Options", {"fields": ("is_active", "display_order")}),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Make the 'name' field read-only when editing an existing SocialMediaAddress.
        """
        if obj:  # editing an existing object
            return ("name",)
        return ()


@admin.register(PhoneAddress, site=admin_site)
class PhoneAddressAdmin(admin.ModelAdmin):
    """
    Admin interface for ContactNumber model with support for listing, filtering,
    searching, ordering, and inline editing of the 'order' field.
    The 'number' field is read-only when editing an existing object.
    """

    list_display = (
        "number",
        "is_active",
        "is_primary",
        "use_for_whatsapp",
        "display_order",
    )
    list_editable = ("display_order",)
    list_filter = ("is_active", "is_primary", "use_for_whatsapp")
    search_fields = ("number",)
    fieldsets = (
        (
            "Phone Number Details",
            {"fields": ("number",)},
        ),
        (
            "Display Options",
            {
                "fields": (
                    "is_active",
                    "is_primary",
                    "use_for_whatsapp",
                    "display_order",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Make the 'number' field read-only when editing an existing PhoneNumber.
        """
        if obj:  # editing an existing object
            return ("number",)
        return ()


@admin.register(EmailAddress, site=admin_site)
class EmailAddresslAdmin(admin.ModelAdmin):
    """
    Admin interface for ContactEmail model with support for listing, filtering,
    searching, ordering, and inline editing of the 'order' field.
    The 'email' field is read-only when editing an existing object.
    """

    list_display = ("email", "is_active", "is_primary", "display_order")
    list_editable = ("display_order",)
    list_filter = ("is_active", "is_primary")
    search_fields = ("email",)
    fieldsets = (
        (
            "Email Address Details",
            {"fields": ("email",)},
        ),
        ("Display Options", {"fields": ("is_active", "is_primary", "display_order")}),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Make the 'email' field read-only when editing an existing EmailAddress.
        """
        if obj:  # editing an existing object
            return ("email",)
        return ()


@admin.register(PhysicalAddress, site=admin_site)
class PhysicalAddressAdmin(admin.ModelAdmin):
    """
    Admin interface for ContactAddress model supporting listing, filtering,
    searching, ordering, and displaying detailed address fields.
    """

    list_display = (
        "label",
        "city",
        "country",
        "use_in_contact_form",
        "is_active",
        "display_order",
    )
    list_editable = ("display_order",)
    list_filter = ("is_active", "use_in_contact_form", "country", "state_province")
    search_fields = ("label", "street_address", "city", "country")
    ordering = ("display_order",)

    fieldsets = (
        (
            "Address Details",
            {
                "fields": (
                    "label",
                    "building",
                    "street_address",
                    "city",
                    "state_province",
                    "postal_code",
                    "country",
                    "map_embed_url",
                )
            },
        ),
        (
            "Display Options",
            {"fields": ("is_active", "use_in_contact_form", "display_order")},
        ),
    )
