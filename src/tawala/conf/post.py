"""Post app initialization

These settings are used throughout ui and utils post initialization,
Centralized here for easy management, ensuring that they are gotten from django.conf instead of own customized settings.py.

Note the order:
- pre.py configures config.py, which in turns is used to configure settings.py.
- We are using config.py to easily manage fetching of settings from either .env or pyproject.toml in the user's project directory
- settings.py is then loaded by Django, from which, in post.py, we centralize the variables that are used within ui and utils.
"""

from django.conf import settings


# TODO: Implement a test or a system checkup that's used by to be part of those system checks done by Django to ensure that SETTING in `getattr(settings, [SETTING])` match in settings.py

PKG_NAME = getattr(settings, "PKG_NAME")
PKG_DIR = getattr(settings, "PKG_DIR")
PKG_VERSION = getattr(settings, "PKG_VERSION")
BASE_DIR = getattr(settings, "BASE_DIR")
CLI_DIR = getattr(settings, "CLI_DIR")
TAILWIND_CLI = getattr(settings, "TAILWIND_CLI")
STORAGE_TOKEN = getattr(settings, "STORAGE_TOKEN")
COMMANDS_BUILD = getattr(settings, "COMMANDS_BUILD")
COMMANDS_INSTALL = getattr(settings, "COMMANDS_INSTALL")
LOGIN_REDIRECT_URL = getattr(settings, "LOGIN_REDIRECT_URL", "/")
