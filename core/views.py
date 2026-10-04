from django.conf import settings
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from products.models import Product


def home(request):
    # « Nos meilleures ventes » : sélection manuelle (case « Meilleure vente » dans l'admin).
    bestsellers = (Product.objects.filter(is_bestseller=True, is_available=True)
                   .prefetch_related("images").order_by("name")[:4])
    # « Nos nouveautés » : sans répéter les meilleures ventes.
    new_arrivals = Product.objects.filter(is_new=True, is_bestseller=False)[:5]
    if not new_arrivals.exists():
        new_arrivals = Product.objects.exclude(is_bestseller=True)[:5] or Product.objects.all()[:5]
    promo_products = Product.objects.on_promo().prefetch_related("images")[:4]
    context = {"new_arrivals": new_arrivals, "promo_products": promo_products, "bestsellers": bestsellers}
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    return render(request, "core/contact.html")


def set_language_custom(request):
    lang = request.GET.get("lang", "fr")
    next_url = request.GET.get("next", "/")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"
    response = redirect(next_url)
    if lang in dict(settings.LANGUAGES):
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    return response
