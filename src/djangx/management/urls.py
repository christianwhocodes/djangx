from django.urls import URLPattern, URLResolver, include, path

from .. import PKG_NAME, PROJECT_MAIN_APP_NAME
from .settings import INSTALLED_APPS

urlpatterns: list[URLPattern | URLResolver] = [
    *(
        [path("__reload__/", include("django_browser_reload.urls"))]
        if "django_browser_reload" in INSTALLED_APPS
        else []
    ),
    path("api/", include(f"{PKG_NAME}.api.urls")),
    path("ui/", include(f"{PKG_NAME}.ui.urls")),
    *(
        [path("", include(f"{PROJECT_MAIN_APP_NAME}.urls"))]
        if PROJECT_MAIN_APP_NAME in INSTALLED_APPS
        else []
    ),
]
