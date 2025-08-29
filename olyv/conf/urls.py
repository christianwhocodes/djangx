from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("__reload__/", include("django_browser_reload.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("base/", include("olyv.base.urls")),
    path("accounts/", include("olyv.accounts.urls")),
    path("addresses/", include("olyv.addresses.urls")),
    path("lists/", include("olyv.lists.urls")),
    path("articles/", include("olyv.articles.urls")),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += [
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]
