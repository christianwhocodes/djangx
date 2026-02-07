from django.conf import settings
from django.urls import URLPattern, URLResolver, include, path

from .. import PROJECT

urlpatterns: list[URLPattern | URLResolver] = [
    *(
        [path("__reload__/", include("django_browser_reload.urls"))]
        if "django_browser_reload" in settings.INSTALLED_APPS
        else []
    ),
    *(
        [path("registration/", include("django.contrib.auth.urls"))]
        if "django.contrib.auth" in settings.INSTALLED_APPS
        else []
    ),
    path("", include(f"{PROJECT.home_app_name}.urls")),
]
