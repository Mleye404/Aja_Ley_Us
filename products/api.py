from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """API REST en lecture seule des produits AJA LEY.

    GET /api/products/       -> liste des produits
    GET /api/products/<id>/  -> détail d'un produit
    """
    queryset = Product.objects.prefetch_related("images").select_related("category")
    serializer_class = ProductSerializer
