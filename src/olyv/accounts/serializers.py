from rest_framework import serializers

from .models import Group, User


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "name",
        ]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "url",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "groups",
        ]
