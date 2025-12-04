"""
ASGI config

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from ...conf.pre import PKG

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{PKG.name}.conf.settings")

application = get_asgi_application()
