from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path

from .. import PKG_NAME
from .settings import ADMIN_URL, BROWSER_RELOAD_URL, INSTALLED_APPS

urlpatterns: list[URLPattern | URLResolver] = [
    *(
        [path(BROWSER_RELOAD_URL, include("django_browser_reload.urls"))]
        if "django_browser_reload" in INSTALLED_APPS
        else []
    ),
    *([path(ADMIN_URL, admin.site.urls)] if "django.contrib.admin" in INSTALLED_APPS else []),
    path("api/", include(f"{PKG_NAME}.api.urls")),
    path("ui/", include(f"{PKG_NAME}.ui.urls")),
    path("", include("home.urls")),
]
