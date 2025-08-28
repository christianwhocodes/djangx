from ...models import GroupDescription, User
from .setup_groups import AbstractGroupSetupCommand


class Command(AbstractGroupSetupCommand):
    """
    Creates the ACCOUNTS_MANAGER group with appropriate permissions for user and group management.

    This command creates a group with full CRUD permissions for account-related models:
    - User: Add, Change, Delete, View
    - GroupDescription: View

    The command is idempotent - it can be run multiple times safely.

    Note: This gives powerful permissions to manage users and groups - assign carefully!
    """

    help = "Create ACCOUNTS_MANAGER group with user and group management permissions"

    groups_config = [
        {
            "id": 19,
            "name": "ACCOUNTS_MANAGER",
            "models_permissions": [
                (User, ["add", "change", "delete", "view"]),
                (GroupDescription, ["view"]),
            ],
            "description": "Full CRUD permissions for users management",
        }
    ]

    def get_model_display_name(self, model_name):
        """Custom model name formatting for auth models."""
        name_mappings = {"user": "User", "groupdescription": "Group Description"}

        return name_mappings.get(model_name.lower(), model_name.title())
