"""
ASGI config

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

from django.core.asgi import get_asgi_application

SERVER_APPLICATION = get_asgi_application()
