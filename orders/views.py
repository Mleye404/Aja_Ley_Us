from django.db import transaction
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from cart.utils import get_or_create_cart
from .constants import (DAKAR_BANLIEUE_HELP, OTHER_LOCALITY, SENEGAL_NAME, SENEGAL_REGIONS, is_senegal,
                        strip_accents, zones_for)
from .forms import CheckoutForm, InternationalCheckoutForm
from .models import Order, OrderItem, ShippingRate
from .utils import remember_guest_order

SESSION_KEY = "checkout_data"
INTERNATIONAL_NOTE = "À confirmer"


def zone_fee(zone):
    return getattr(settings, zone["fee_setting"])


def compute_shipping(country, city, zone=""):
    """Retourne (frais, note).

    Sénégal — zones de livraison AJA LEY :
      Dakar : Dakar-ville 2 000 / Banlieue dakaroise 4 000 ; Thiès : Thiès-ville 1 000 / autre
      localité 2 000 ; toutes les autres régions : 2 000 FCFA (un tarif défini dans l'admin pour
      une région sans zones la remplace).
    International : AUCUN tarif automatique -> « À confirmer »."""
    if not is_senegal(country):
        return 0, INTERNATIONAL_NOTE
    region_key = strip_accents(city)
    region = next((r for r in SENEGAL_REGIONS if strip_accents(r) == region_key), None)
    zones = zones_for(region)
    if zones:
        chosen = next((z for z in zones if strip_accents(z["name"]) == strip_accents(zone)), None)
        # Sans zone (anciennes commandes) : tarif de la zone « ville ».
        return zone_fee(chosen or zones[0]), ""
    for rate in ShippingRate.objects.all():          # surcharge facultative depuis l'admin
        if strip_accents(rate.city) == region_key:
            return rate.fee, ""
    return settings.SHIPPING_OTHER_REGIONS, ""


def shipping_config():
    """Configuration des frais pour le checkout (calcul dynamique côté navigateur) :
    {région: {"fee": n}} ou {région: {"zones": [{name, fee, locality, localities}], "help": ...}}."""
    config = {}
    for region in SENEGAL_REGIONS:
        zones = zones_for(region)
        if zones:
            config[region] = {"zones": [{"name": z["name"], "fee": zone_fee(z), "locality": z["locality"],
                                         "localities": z["localities"]} for z in zones]}
            if region == "Dakar":
                config[region]["help"] = DAKAR_BANLIEUE_HELP
        else:
            config[region] = {"fee": compute_shipping(SENEGAL_NAME, region)[0]}
    return config


def _checkout(request, international):
    """Étape 1 : informations de la cliente. Deux parcours : Sénégal (région en liste) et international."""
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")
    if not items.exists():
        messages.warning(request, "Votre panier est vide.")
        return redirect("cart:view_cart")

    initial = {}
    if request.user.is_authenticated:
        initial = {"first_name": request.user.first_name, "last_name": request.user.last_name,
                   "email": request.user.email}
        profile = getattr(request.user, "profile", None)
        if profile and profile.phone:
            initial["phone"] = profile.phone

    # Retour depuis le récapitulatif : on re-remplit le formulaire du même parcours.
    saved = request.session.get(SESSION_KEY)
    if saved and bool(saved.get("international")) == international:
        initial.update({k: saved[k] for k in ("first_name", "last_name", "phone", "email",
                                              "district", "extra_info") if k in saved})
        if international:
            initial.update({k: saved[k] for k in ("country", "city") if k in saved})
        else:
            if saved.get("city") in SENEGAL_REGIONS:
                initial["region"] = saved["city"]
            initial["delivery_zone"] = saved.get("delivery_zone", "")
            zone = next((z for z in zones_for(saved.get("city")) if z["name"] == saved.get("delivery_zone")), None)
            locality = saved.get("locality", "")
            if zone and zone["locality"] and locality:
                if locality in zone["localities"] and locality != OTHER_LOCALITY:
                    initial["locality"] = locality
                else:                     # localité saisie librement via « Autre »
                    initial["locality"] = OTHER_LOCALITY
                    initial["locality_other"] = locality

    FormClass = InternationalCheckoutForm if international else CheckoutForm
    if request.method == "POST":
        form = FormClass(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            if international:
                data["international"] = True
            else:
                data["city"] = data.pop("region")        # Sénégal : la « ville » enregistrée = la région
                data["country"] = SENEGAL_NAME
                data["international"] = False
            request.session[SESSION_KEY] = data
            return redirect("orders:recap")
    else:
        form = FormClass(initial=initial)

    context = {"form": form, "cart": cart, "items": items, "international": international,
               "subtotal": cart.subtotal}
    if not international:
        config = shipping_config()
        region = form["region"].value() or ""
        region = region if region in config else ""
        zones = config[region].get("zones", []) if region else []
        zone_name = form["delivery_zone"].value() or ""
        zone = next((z for z in zones if z["name"] == zone_name), None)
        if region and not zones:
            fee = config[region]["fee"]
        else:
            fee = zone["fee"] if zone else None
        context.update({
            "shipping_config": config,
            "selected_region": region,
            "zone_options": zones,
            "selected_zone": zone["name"] if zone else "",
            "zone_help": config[region].get("help", "") if region else "",
            "locality_visible": bool(zone and zone["locality"]),
            "locality_options": zone["localities"] if zone and zone["locality"] else [],
            "selected_locality": form["locality"].value() or "",
            "other_visible": bool(zone and zone["locality"] and form["locality"].value() == OTHER_LOCALITY),
            "shipping_fee": fee,
            "total": cart.subtotal + (fee or 0),
        })
    return render(request, "orders/checkout.html", context)


def checkout(request):
    """Commande au Sénégal."""
    return _checkout(request, international=False)


def checkout_international(request):
    """Commande depuis l'international (option secondaire du checkout)."""
    return _checkout(request, international=True)


def recap(request):
    """Étape 2 : récapitulatif de la commande avant validation finale."""
    data = request.session.get(SESSION_KEY)
    cart = get_or_create_cart(request)
    items = cart.items.select_related("product")
    if not data or not items.exists():
        messages.warning(request, "Merci de renseigner vos informations avant de continuer.")
        return redirect("orders:checkout")

    international = not is_senegal(data["country"])
    fee, note = compute_shipping(data["country"], data["city"], data.get("delivery_zone", ""))
    subtotal = cart.subtotal

    if request.method == "POST":
        unavailable = [i.product.name for i in items if not i.product.is_available]
        if unavailable:
            # Un produit passé en rupture depuis l'ajout au panier n'est plus commandable.
            messages.error(request, "Ces produits sont en rupture de stock : " + ", ".join(unavailable)
                           + ". Retirez-les du panier pour continuer.")
            return redirect("cart:view_cart")
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=data["first_name"], last_name=data["last_name"],
                phone=data["phone"], email=data["email"],
                country=data["country"], city=data["city"], district=data["district"],
                delivery_zone=data.get("delivery_zone", ""), locality=data.get("locality", ""),
                extra_info=data["extra_info"],
                shipping_fee=fee, shipping_note=note,
                subtotal=subtotal, total=subtotal + fee,
            )
            for item in items:
                OrderItem.objects.create(
                    order=order, product=item.product, product_name=item.product.name,
                    unit_price=item.product.current_price, quantity=item.quantity,
                    size=item.size, length=item.length,
                    bust=item.bust, waist=item.waist, hips=item.hips, shoulders=item.shoulders,
                    desired_length=item.desired_length, sleeve_length=item.sleeve_length,
                    extra_notes=item.extra_notes,
                )
            cart.is_ordered = True
            cart.save()
        if not request.user.is_authenticated:
            remember_guest_order(request, order)
        del request.session[SESSION_KEY]
        return redirect("orders:confirmation", reference=order.reference)

    context = {
        "data": data, "items": items, "subtotal": subtotal, "international": international,
        "shipping_fee": fee, "shipping_note": note, "total": subtotal + fee,
    }
    return render(request, "orders/recap.html", context)


def confirmation(request, reference):
    """Étape 3 : commande enregistrée — la cliente envoie le récapitulatif via WhatsApp."""
    order = get_object_or_404(Order.objects.prefetch_related("items"), reference=reference)
    # Commande liée à un compte : visible par sa propriétaire ou le staff. Commande invitée : via sa référence.
    if order.user_id and not (request.user.is_authenticated
                              and (request.user.pk == order.user_id or request.user.is_staff)):
        raise Http404()
    return render(request, "orders/confirmation.html", {"order": order})


@login_required
def my_orders(request):
    """Commandes en cours de la cliente connectée (Livrée ou Annulée : elles disparaissent de la liste)."""
    orders = (Order.objects.filter(user=request.user)
              .exclude(status__in=Order.FINAL_STATUSES)
              .prefetch_related("items").order_by("-created_at"))
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, number):
    """Détail et suivi d'une commande : 404 si elle appartient à une autre cliente (le staff a accès à tout)."""
    qs = Order.objects.prefetch_related("items")
    if not request.user.is_staff:
        qs = qs.filter(user=request.user)
    order = get_object_or_404(qs, number=number)
    return render(request, "orders/order_detail.html", {"order": order})
