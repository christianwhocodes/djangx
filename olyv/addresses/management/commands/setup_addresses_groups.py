from olyv.accounts.management.commands.setup_groups import AbstractGroupSetupCommand

from ...models import EmailAddress, PhoneAddress, PhysicalAddress, SocialMediaAddress


class Command(AbstractGroupSetupCommand):
    """
    Creates the ADDRESSES_MANAGER group with appropriate permissions for address management.

    This command creates a group with full CRUD permissions for all address-related models:
    - SocialMediaAddress: Add, Change, Delete, View
    - PhoneAddress: Add, Change, Delete, View
    - EmailAddress: Add, Change, Delete, View
    - PhysicalAddress: Add, Change, Delete, View

    The command is idempotent - it can be run multiple times safely.
    """

    help = "Create ADDRESSES_MANAGER group with address management permissions"

    groups_config = [
        {
            "id": 20,
            "name": "ADDRESSES_MANAGER",
            "models_permissions": [
                (SocialMediaAddress, ["add", "change", "delete", "view"]),
                (PhoneAddress, ["add", "change", "delete", "view"]),
                (EmailAddress, ["add", "change", "delete", "view"]),
                (PhysicalAddress, ["add", "change", "delete", "view"]),
            ],
            "description": "Full CRUD permissions for all address types",
        }
    ]

    def get_model_display_name(self, model_name):
        """Custom model name formatting for address models."""
        # Handle the specific address model names
        name_mappings = {
            "socialmediaaddress": "Social Media Address",
            "phoneaddress": "Phone Address",
            "emailaddress": "Email Address",
            "physicaladdress": "Physical Address",
        }

        return name_mappings.get(model_name.lower(), model_name.title())
