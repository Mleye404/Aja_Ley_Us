from django.conf import settings
from products.models import Product


def site_context(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_SLOGAN": settings.SITE_SLOGAN,
        "WHATSAPP_SENEGAL": settings.WHATSAPP_SENEGAL,
        "WHATSAPP_SENEGAL_DISPLAY": settings.WHATSAPP_SENEGAL_DISPLAY,
        "WHATSAPP_INTL": settings.WHATSAPP_INTL,
        "WHATSAPP_INTL_DISPLAY": settings.WHATSAPP_INTL_DISPLAY,
        "WHATSAPP_LINK": settings.WHATSAPP_LINK,
        "INSTAGRAM_HANDLE": settings.INSTAGRAM_HANDLE,
        "INSTAGRAM_LINK": settings.INSTAGRAM_LINK,
        # La rubrique « Promotions » n'apparaît que s'il y a au moins un produit en promotion.
        "has_promotions": Product.objects.on_promo().exists(),
    }
