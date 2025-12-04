"""
WSGI config

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from ...conf.pre import PKG

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{PKG.name}.conf.settings")

application = get_wsgi_application()
