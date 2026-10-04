from rest_framework import serializers
from .models import Product, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "order"]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()
    current_price = serializers.ReadOnlyField()
    is_on_promo = serializers.ReadOnlyField()
    discount_percent = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "category", "description", "price",
                  "current_price", "is_on_promo", "discount_percent",
                  "color", "is_available", "is_featured", "is_new", "images"]
