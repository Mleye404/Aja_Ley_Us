from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Favorite


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "order", "preview")
    readonly_fields = ("preview",)

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.image.url)
        return "—"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "promo_active", "promo_price", "discount_display",
                    "is_available", "is_featured", "is_new", "is_bestseller", "photo_count")
    list_filter = ("category", "promo_active", "is_available", "is_featured", "is_new", "is_bestseller")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    list_editable = ("promo_active", "promo_price", "is_available", "is_featured", "is_new", "is_bestseller")
    readonly_fields = ("discount_display",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "description", "color")}),
        ("Prix et promotion", {
            "fields": ("price", "promo_active", "promo_price", "discount_display"),
            "description": "Le prix normal est toujours conservé : désactiver la promotion le rétablit "
                           "automatiquement. Le pourcentage de réduction est calculé tout seul.",
        }),
        ("Disponibilité et mise en avant", {"fields": ("is_available", "is_featured", "is_new", "is_bestseller")}),
    )

    @admin.display(description="Photos")
    def photo_count(self, obj):
        return obj.images.count()

    @admin.display(description="Réduction")
    def discount_display(self, obj):
        if obj.pk and obj.promo_active and obj.promo_price and obj.promo_price < obj.price:
            return f"-{(200 * (obj.price - obj.promo_price) + obj.price) // (2 * obj.price)} %"
        return "—"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
