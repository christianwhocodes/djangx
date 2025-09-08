from django.urls import path

from .views import EmailUsAPIView

urlpatterns = [
    path("email-us/", EmailUsAPIView.as_view(), name="email-us"),
]
