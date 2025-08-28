from olyv.accounts.management.commands.setup_groups import AbstractGroupSetupCommand

from ...models import Article, ArticleCategory, ArticleTag


class Command(AbstractGroupSetupCommand):
    """
    Creates article management groups with appropriate permissions:

    ARTICLES_OPERATOR:
    - Articles: Full CRUD (with custom admin logic to restrict delete to own articles)
    - Categories: View only (cannot create/modify site-wide categories)
    - Tags: Add, Change, View (cannot delete to avoid breaking other articles)

    ARTICLES_MANAGER:
    - Articles: Full CRUD (can manage any article)
    - Categories: Full CRUD (can manage site-wide categories)
    - Tags: Full CRUD (can manage all tags)

    The command is idempotent - it can be run multiple times safely.
    """

    help = "Create ARTICLES_OPERATOR and ARTICLES_MANAGER groups with appropriate permissions"

    groups_config = [
        {
            "id": 22,
            "name": "ARTICLES_OPERATOR",
            "models_permissions": [
                (
                    ArticleCategory,
                    ["view"],
                ),  # View only - can't modify site-wide categories
                (
                    ArticleTag,
                    ["add", "change", "view", "delete"],
                ),  # Can create/edit but not delete tags
                (
                    Article,
                    ["add", "change", "delete", "view"],
                ),  # Full CRUD (delete restricted in admin)
            ],
            "description": "Authors can create/edit their own articles, manage tags, but only view categories. Categories are managed by ARTICLES_MANAGER group.",
        },
        {
            "id": 23,
            "name": "ARTICLES_MANAGER",
            "models_permissions": [
                (
                    ArticleCategory,
                    ["add", "change", "delete", "view"],
                ),  # Full category management
                (
                    ArticleTag,
                    ["add", "change", "delete", "view"],
                ),  # Full tag management
                (
                    Article,
                    ["add", "change", "delete", "view"],
                ),  # Full article management
            ],
            "description": "Full management permissions for all articles, categories, and tags",
        },
    ]

    def get_model_display_name(self, model_name):
        """Custom model name formatting for article models."""
        name_mappings = {
            "articlecategory": "Article Category",
            "articletag": "Article Tag",
            "article": "Article",
        }

        return name_mappings.get(model_name.lower(), model_name.title())
