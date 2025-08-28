import logging
from importlib import import_module

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "olyv.accounts"

    def ready(self):
        # Import signals to ensure they are registered
        try:
            import_module(f"{self.name}.signals")
        except ImportError as e:
            logger.error(f"Error importing signals: {e}")
