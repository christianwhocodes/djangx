from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import Group, User
from .serializers import GroupSerializer, UserSerializer


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "groups",
    ]
