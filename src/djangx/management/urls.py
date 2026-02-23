"""URL configuration."""

from django.urls import URLPattern, URLResolver, include, path

from .. import PROJECT
from .enums import AppEnum
from .conf import INSTALLED_APPS

urlpatterns: list[URLPattern | URLResolver] = [
    *(
        [path("__reload__/", include(f"{AppEnum.BROWSER_RELOAD.value}.urls"))]
        if AppEnum.BROWSER_RELOAD in INSTALLED_APPS
        else []
    ),
    *(
        [path("registration/", include(f"{AppEnum.AUTH.value}.urls"))]
        if AppEnum.AUTH in INSTALLED_APPS
        else []
    ),
    path("", include(f"{PROJECT.home_app_name}.urls")),
]
