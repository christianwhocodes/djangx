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
