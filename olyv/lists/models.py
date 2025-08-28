from django.db import models

from olyv.base.models import (
    AbstractBootstrapIcon,
    AbstractCreatedAtUpdatedAt,
    AbstractDisplayOrder,
)


class ListCategory(AbstractCreatedAtUpdatedAt):
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "List categories"

    name = models.CharField(
        max_length=255,
        help_text="Category name that groups related list items (e.g., 'Electronics', 'Furniture').",
    )

    def __str__(self):
        return self.name


class ListItem(AbstractDisplayOrder, AbstractBootstrapIcon, AbstractCreatedAtUpdatedAt):
    class Meta:
        ordering = ["display_order", "name"]

    category = models.ForeignKey(
        ListCategory,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(
        max_length=255,
        help_text="Name of the item.",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of this item, including features or specifications (optional).",
    )

    def __str__(self):
        return self.name
