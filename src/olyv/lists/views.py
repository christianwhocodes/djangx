# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework import viewsets

# from .models import ListCategory, ListItem
# from .serializers import ListCategorySerializer, ListItemSerializer


# class ListCategoryViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = ListCategory.objects.all()
#     serializer_class = ListCategorySerializer


# class ListItemViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = ListItem.objects.all()
#     serializer_class = ListItemSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["category"]
