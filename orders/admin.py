from django.contrib import admin
from .models import Order, OrderItem, ShippingRate


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit_price", "quantity", "size", "length", "bust", "waist", "hips",
                        "shoulders", "desired_length", "sleeve_length", "extra_notes")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number_display", "full_name", "account", "products_summary", "total", "status",
                    "created_at", "expected_delivery_date", "city", "country")
    list_filter = ("status", "country", "city")
    search_fields = ("number", "reference", "first_name", "last_name", "phone", "email")
    list_editable = ("status", "expected_delivery_date")
    list_select_related = ("user",)
    readonly_fields = ("number", "reference", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    def get_search_results(self, request, queryset, search_term):
        # Permet de chercher « #AJL-00042 » comme on le lit dans le message WhatsApp.
        return super().get_search_results(request, queryset, search_term.lstrip("#"))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")

    @admin.display(description="N° commande", ordering="number")
    def number_display(self, obj):
        return obj.display_number

    @admin.display(description="Compte")
    def account(self, obj):
        return obj.user.get_username() if obj.user else "Invitée"

    @admin.display(description="Produits")
    def products_summary(self, obj):
        return ", ".join(f"{i.product_name} ×{i.quantity}" for i in obj.items.all())


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("city", "fee")
