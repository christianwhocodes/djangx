from django.db import models
from django.templatetags.static import static


class AbstractDisplayOrder(models.Model):
    display_order = models.PositiveIntegerField(
        default=1,
        help_text="Display order (lower numbers - zero included - appear first)",
    )

    class Meta:
        abstract = True


class AbstractBootstrapIcon(models.Model):
    bootstrap_icon = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional Bootstrap icon class. Example: 'bi bi-cart' for a shopping cart icon. Find icons at [Bootstrap Icons](https://icons.getbootstrap.com/).",
    )

    class Meta:
        abstract = True


class AbstractCreatedAtUpdatedAt(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time last updated.",
    )

    class Meta:
        abstract = True


class AbstractImage(models.Model):
    class Meta:
        abstract = True

    image = models.ImageField(
        upload_to="images/",
        blank=True,
        null=True,
        help_text="Optional Image.",
    )
    image_alt_text = models.CharField(
        max_length=255, blank=True, help_text="Alternative text for accessibility."
    )

    @property
    def image_url(self):
        """Return the URL of the image if it exists."""
        if self.image:
            return self.image.url
        return static("base/images/default.png")
