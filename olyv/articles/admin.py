from django.contrib import admin
from django.core.exceptions import PermissionDenied

from olyv.base.adminsite import admin_site

from .forms import ArticleForm
from .models import Article, ArticleCategory, ArticleTag


@admin.register(Article, site=admin_site)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "date_created")
    list_filter = ("category", "date_created", "author")
    search_fields = ("title", "content")
    readonly_fields = ("author",)
    form = ArticleForm
    fieldsets = (
        ("Basic Information", {"fields": ("title", "content", "image")}),
        ("Categorization", {"fields": ("category", "tags"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Filter articles based on user permissions."""
        qs = super().get_queryset(request)

        # ARTICLES_MANAGER can see all articles
        if request.user.groups.filter(name="ARTICLES_MANAGER").exists():
            return qs

        # ARTICLES_OPERATOR can only see their own articles
        if request.user.groups.filter(name="ARTICLES_OPERATOR").exists():
            return qs.filter(author=request.user)

        # Superusers see everything
        if request.user.is_superuser:
            return qs

        # Others see nothing (fallback)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        """Check if user can change this specific article."""
        if not super().has_change_permission(request, obj):
            return False

        # No specific object, check general permission
        if obj is None:
            return True

        # ARTICLES_MANAGER can change any article
        if request.user.groups.filter(name="ARTICLES_MANAGER").exists():
            return True

        # ARTICLES_OPERATOR can only change their own articles
        if request.user.groups.filter(name="ARTICLES_OPERATOR").exists():
            return obj.author == request.user

        # Superuser can change anything
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete this specific article."""
        if not super().has_delete_permission(request, obj):
            return False

        # No specific object, check general permission
        if obj is None:
            return True

        # ARTICLES_MANAGER can delete any article
        if request.user.groups.filter(name="ARTICLES_MANAGER").exists():
            return True

        # ARTICLES_OPERATOR can only delete their own articles
        if request.user.groups.filter(name="ARTICLES_OPERATOR").exists():
            return obj.author == request.user

        # Superuser can delete anything
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """Set author and validate permissions."""
        # Set the author to the current user when adding a new article
        if not change:  # Only set author if this is a new article
            obj.author = request.user
        # If the author is not set, ensure it is set to the current user
        elif not obj.author:
            obj.author = request.user
        else:
            # Prevent ARTICLES_OPERATOR from changing articles they don't own
            if (
                request.user.groups.filter(name="ARTICLES_OPERATOR").exists()
                and not request.user.groups.filter(name="ARTICLES_MANAGER").exists()
                and not request.user.is_superuser
                and obj.author != request.user
            ):
                raise PermissionDenied("You can only edit your own articles.")

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Validate delete permissions before deletion."""
        if (
            request.user.groups.filter(name="ARTICLES_OPERATOR").exists()
            and not request.user.groups.filter(name="ARTICLES_MANAGER").exists()
            and not request.user.is_superuser
            and obj.author != request.user
        ):
            raise PermissionDenied("You can only delete your own articles.")

        super().delete_model(request, obj)


@admin.register(ArticleCategory, site=admin_site)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    def has_add_permission(self, request):
        """Only ARTICLES_MANAGER can add categories."""
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="ARTICLES_MANAGER").exists()

    def has_change_permission(self, request, obj=None):
        """Only ARTICLES_MANAGER can change categories."""
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="ARTICLES_MANAGER").exists()

    def has_delete_permission(self, request, obj=None):
        """Only ARTICLES_MANAGER can delete categories."""
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="ARTICLES_MANAGER").exists()


@admin.register(ArticleTag, site=admin_site)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    def has_delete_permission(self, request, obj=None):
        """Only ARTICLES_MANAGER can delete tags."""
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="ARTICLES_MANAGER").exists()
