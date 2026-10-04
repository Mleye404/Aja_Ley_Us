from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from cart.sizes import LENGTHS, SIZES, SIZE_GUIDE
from .models import Product, Category, Favorite


def catalog(request):
    products = Product.objects.select_related("category").prefetch_related("images").with_effective_price()

    # Rubrique « Promotions » : n'existe que s'il y a au moins un produit en promotion.
    promo_only = request.GET.get("promo") == "1"
    if promo_only:
        if not Product.objects.on_promo().exists():
            return redirect("products:catalog")
        products = products.on_promo()

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    cat_slug = request.GET.get("categorie", "")
    if cat_slug:
        products = products.filter(category__slug=cat_slug)

    prix = request.GET.get("prix", "")
    if prix == "moins15":
        products = products.filter(effective_price__lt=15000)
    elif prix == "15a25":
        products = products.filter(effective_price__gte=15000, effective_price__lte=25000)
    elif prix == "plus25":
        products = products.filter(effective_price__gt=25000)

    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list("product_id", flat=True))

    context = {
        "products": products,
        "categories": Category.objects.all(),
        "query": query,
        "selected_categorie": cat_slug,
        "selected_prix": prix,
        "favorite_ids": favorite_ids,
        "promo_only": promo_only,
    }
    return render(request, "products/catalog.html", context)


def detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related("images"), slug=slug)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, product=product).exists()
    related = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]
    context = {"product": product, "is_favorite": is_favorite, "related": related,
               "sizes": SIZES, "lengths": LENGTHS, "size_guide": SIZE_GUIDE}
    return render(request, "products/detail.html", context)


@login_required
@require_POST
def toggle_favorite(request, slug):
    product = get_object_or_404(Product, slug=slug)
    fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
        messages.info(request, "Produit retiré de vos favoris.")
    else:
        messages.success(request, "Produit ajouté à vos favoris.")
    referer = request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect("products:catalog")


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related("product")
    return render(request, "products/favorites.html", {"favorites": favorites})
