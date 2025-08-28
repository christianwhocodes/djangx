from rest_framework import serializers

from .models import ListCategory, ListItem


class ListCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListCategory
        fields = [
            "id",
            "name",
        ]


class ListItemSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.HyperlinkedRelatedField(
        view_name="listcategory-detail", queryset=ListCategory.objects.all()
    )

    class Meta:
        model = ListItem
        fields = [
            "url",
            "name",
            "description",
            "bootstrap_icon",
            "category",
        ]
