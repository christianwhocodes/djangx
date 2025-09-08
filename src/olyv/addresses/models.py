from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from olyv.base.models import AbstractDisplayOrder


class AbstractAddress(models.Model):
    is_active = models.BooleanField(default=True, help_text="Whether this should be displayed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SocialMediaAddress(AbstractAddress, AbstractDisplayOrder):
    """
    Represents a social media link with associated Bootstrap icon class,
    display status, and display order.
    """

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Social Media Addresses"

    MODEL_CHOICES = [
        ("facebook", "Facebook"),
        ("twitter", "X (formerly Twitter)"),
        ("instagram", "Instagram"),
        ("linkedin", "LinkedIn"),
        ("youtube", "YouTube"),
        ("tiktok", "TikTok"),
        ("pinterest", "Pinterest"),
        ("snapchat", "Snapchat"),
        ("discord", "Discord"),
        ("telegram", "Telegram"),
        ("github", "GitHub"),
        ("reddit", "Reddit"),
        ("twitch", "Twitch"),
    ]

    ICON_MAPPING = {
        "facebook": "bi bi-facebook",
        "twitter": "bi bi-twitter-x",
        "instagram": "bi bi-instagram",
        "linkedin": "bi bi-linkedin",
        "youtube": "bi bi-youtube",
        "tiktok": "bi bi-tiktok",
        "pinterest": "bi bi-pinterest",
        "snapchat": "bi bi-snapchat",
        "discord": "bi bi-discord",
        "telegram": "bi bi-telegram",
        "github": "bi bi-github",
        "reddit": "bi bi-reddit",
        "twitch": "bi bi-twitch",
    }

    name = models.CharField(max_length=20, choices=MODEL_CHOICES, unique=True)
    icon = models.CharField(
        editable=False,
        max_length=50,
        blank=True,
        help_text="Bootstrap icon class (auto-populated based on name)",
    )  # *: NOTE that we're nor using the AbstractBootstrapIcon model here
    url = models.URLField(help_text="URL to your selected social media profile")

    def save(self, *args, **kwargs):
        """Auto-assign icon based on the platform name before saving."""
        if self.name in self.ICON_MAPPING:
            self.icon = self.ICON_MAPPING[self.name]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_name_display()} - {self.url}"

    @property
    def display_name(self):
        """Returns the human-readable name of the social media platform"""
        return self.get_name_display()

    @property
    def icon_html(self):
        """Returns HTML for the Bootstrap icon"""
        if self.icon:
            return f'<i class="{self.icon}"></i>'
        return ""


class PhoneAddress(AbstractAddress, AbstractDisplayOrder):
    """
    Stores phone numbers with metadata such as primary use, WhatsApp usage,
    display status, and order.
    """

    class Meta:
        ordering = ["display_order", "number"]
        verbose_name_plural = "Phone Addresses"

    number = PhoneNumberField(
        region="KE",
        help_text="Phone number (e.g., +254712345678 or 0712345678)",
        unique=True,
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as primary phone number. If is_active is False, this will be ignored.",
    )
    use_for_whatsapp = models.BooleanField(
        default=False,
        help_text="Whether this phone number should be used for WhatsApp. If is_active is False, this will be ignored.",
    )

    def save(self, *args, **kwargs):
        """
        Enforces business rules:
        - Only one primary number allowed
        - Only one WhatsApp number allowed
        - If inactive, disables primary and WhatsApp flags
        """
        if not self.is_active:
            self.is_primary = False
            self.use_for_whatsapp = False

        if self.is_primary:
            PhoneAddress.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)

        if self.use_for_whatsapp:
            PhoneAddress.objects.filter(use_for_whatsapp=True).exclude(pk=self.pk).update(
                use_for_whatsapp=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.international_format

    @property
    def formatted_number(self):
        """Returns the formatted phone number"""
        return str(self.number)

    @property
    def national_format(self):
        """Returns phone number in national format"""
        return self.number.as_national if self.number else ""

    @property
    def international_format(self):
        """Returns phone number in international format"""
        return self.number.as_international if self.number else ""

    @property
    def tel_link(self):
        """Returns a tel: link for the phone number"""
        return f"tel:{self.number}"

    @property
    def whatsapp_link(self):
        """Returns a WhatsApp link for the phone number"""
        if self.use_for_whatsapp and self.number:
            clean_number = str(self.number).replace("+", "").replace(" ", "")
            return f"https://wa.me/{clean_number}"
        return ""


class EmailAddress(AbstractAddress, AbstractDisplayOrder):
    """
    Stores email addresses with metadata for display, priority,
    and ordering.
    """

    class Meta:
        ordering = ["display_order", "email"]
        verbose_name_plural = "Email Addresses"

    email = models.EmailField(
        help_text="Email address (e.g., user@example.com)",
        unique=True,
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as email address to be used in contact forms. If is_active is False, this will be ignored.",
    )

    def save(self, *args, **kwargs):
        """
        Ensures only one email is set as primary and disables primary
        if email is not active.
        """
        if not self.is_active:
            self.is_primary = False

        if self.is_primary:
            EmailAddress.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def mailto_link(self):
        """Returns a mailto: link for the email address"""
        return f"mailto:{self.email}"


class PhysicalAddress(AbstractAddress, AbstractDisplayOrder):
    """
    Stores physical addresses, with optional Google Maps embed URLs,
    display order, and contact form preferences.
    """

    class Meta:
        ordering = ["display_order", "label", "city"]
        verbose_name_plural = "Physical Addresses"

    label = models.CharField(
        max_length=100,
        help_text="Custom label for this address e.g Main Office Address",
        unique=True,
    )
    building = models.CharField(
        max_length=100,
        blank=True,
        help_text="Building name or number (e.g., Britam Tower, Block A)",
    )
    street_address = models.CharField(
        max_length=255,
        help_text="Street address including house number and street name",
        blank=True,
    )
    city = models.CharField(max_length=100, help_text="City name", blank=True)
    state_province = models.CharField(
        max_length=100,
        blank=True,
        help_text="State, province, or county (e.g., Vihiga County)",
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="ZIP code, postal code, or equivalent",
    )
    country = models.CharField(max_length=100, default="Kenya", help_text="Country name", blank=True)
    map_embed_url = models.URLField(
        blank=True,
        max_length=500,
        help_text="Google Maps/Other map provider embed URL for displaying in iframes",
    )
    use_in_contact_form = models.BooleanField(
        default=False,
        help_text="Mark this as the address to use in contact forms and maps. Only one active address can be selected.",
    )

    def save(self, *args, **kwargs):
        """
        Ensures only one address is marked for contact form use.
        Automatically disables this flag if the address is inactive.
        """
        if not self.is_active:
            self.use_in_contact_form = False

        if self.use_in_contact_form:
            PhysicalAddress.objects.filter(use_in_contact_form=True).exclude(pk=self.pk).update(
                use_in_contact_form=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.label if self.label else self.city

    @property
    def full_address(self):
        """Returns the full formatted address string"""
        parts = [self.street_address, self.city]
        if self.state_province:
            parts.append(self.state_province)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)

    @property
    def short_address(self):
        """Returns a shorter city + country format"""
        return f"{self.city}, {self.country}"

    @property
    def google_maps_url(self):
        """Generates a Google Maps search URL for the full address"""
        import urllib.parse

        query = urllib.parse.quote_plus(self.full_address)
        return f"https://www.google.com/maps/search/?api=1&query={query}"
