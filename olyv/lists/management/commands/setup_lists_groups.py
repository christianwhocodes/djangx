from olyv.accounts.management.commands.setup_groups import AbstractGroupSetupCommand

from ...models import ListItem


class Command(AbstractGroupSetupCommand):
    """
    Creates the LISTS_MANAGER group with appropriate permissions for list management.

    This command creates a group with full CRUD permissions for list-related models:
    - ListItem: Add, Change, Delete, View

    The command is idempotent - it can be run multiple times safely.
    """

    help = "Create LISTS_MANAGER group with list management permissions"

    groups_config = [
        {
            "id": 21,
            "name": "LISTS_MANAGER",
            "models_permissions": [
                (ListItem, ["add", "change", "delete", "view"]),
            ],
            "description": "Full CRUD permissions for list items",
        }
    ]

    def get_model_display_name(self, model_name):
        """Custom model name formatting for list models."""
        name_mappings = {"listitem": "List Item"}

        return name_mappings.get(model_name.lower(), model_name.title())
