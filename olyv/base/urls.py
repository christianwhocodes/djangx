from django.urls import path

from .adminsite import admin_site

urlpatterns = [
    path("admin/", admin_site.urls, name="admin:index"),
]
