from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from products.api import ProductViewSet
from core.views import set_language_custom

admin.site.site_header = "AJA LEY — Administration"
admin.site.site_title = "AJA LEY Admin"
admin.site.index_title = "Gestion de la boutique AJA LEY"

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("langue/", set_language_custom, name="set_language"),
    path("api/", include(router.urls)),
    path("", include("core.urls")),
    path("boutique/", include("products.urls")),
    path("panier/", include("cart.urls")),
    path("commandes/", include("orders.urls")),
    # Paiement manuel via WhatsApp : l'app `payments` est gardée pour une future V2, non routée.
    # path("paiement/", include("payments.urls")),
    path("compte/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
