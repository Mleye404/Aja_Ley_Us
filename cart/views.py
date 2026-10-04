from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from .models import CartItem
from .forms import SizeForm
from .sizes import LENGTHS, SIZES, SIZE_GUIDE
from .utils import get_or_create_cart


def add_to_cart(request, slug):
    """Ajout au panier depuis la fiche produit : la cliente a choisi une taille (XS à XXL) et une longueur."""
    product = get_object_or_404(Product, slug=slug)
    if not product.is_available:
        # Un produit en rupture n'est pas commandable, même en tapant l'URL directement.
        messages.error(request, "Ce produit est actuellement en rupture de stock.")
        return redirect(product.get_absolute_url())
    if request.method != "POST":
        messages.info(request, "Choisissez votre taille et votre longueur pour ajouter cet article au panier.")
        return redirect(product.get_absolute_url())

    form = SizeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Veuillez choisir votre taille et votre longueur.")
        return redirect(product.get_absolute_url())

    size, length = form.cleaned_data["size"], form.cleaned_data["length"]
    cart = get_or_create_cart(request)
    # Une ligne par produit + taille + longueur (deux tailles différentes = deux lignes).
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, size=size, length=length, defaults={"quantity": 1})
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"« {product.name} » ({size}, {length}) a été ajouté à votre panier.")
    return redirect("cart:view_cart")


def view_cart(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product").prefetch_related("product__images")
    return render(request, "cart/cart.html", {"cart": cart, "items": items})


@require_POST
def update_quantity(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    action = request.POST.get("action")
    if action == "increase":
        item.quantity += 1
        item.save()
    elif action == "decrease":
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()
    return redirect("cart:view_cart")


@require_POST
def remove_item(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    messages.info(request, "Produit retiré du panier.")
    return redirect("cart:view_cart")


def edit_size(request, item_id):
    """Modifier la taille / la longueur d'un article déjà dans le panier."""
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if request.method == "POST":
        form = SizeForm(request.POST)
        if form.is_valid():
            size, length = form.cleaned_data["size"], form.cleaned_data["length"]
            other = (CartItem.objects.filter(cart=cart, product=item.product, size=size, length=length)
                     .exclude(pk=item.pk).first())
            if other:                      # même produit, même taille, même longueur : on fusionne
                other.quantity += item.quantity
                other.save()
                item.delete()
            else:
                item.size, item.length = size, length
                item.save()
            messages.success(request, "Taille mise à jour.")
            return redirect("cart:view_cart")
    else:
        form = SizeForm(initial={"size": item.size, "length": item.length})
    return render(request, "cart/size_edit.html", {
        "form": form, "product": item.product, "item": item,
        "sizes": SIZES, "lengths": LENGTHS, "size_guide": SIZE_GUIDE,
        "selected_size": form["size"].value() or "", "selected_length": form["length"].value() or "",
    })
