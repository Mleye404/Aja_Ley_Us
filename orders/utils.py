from .models import Order

GUEST_ORDERS_KEY = "guest_orders"


def remember_guest_order(request, order):
    """Cliente non connectée : on garde en session les commandes passées depuis ce navigateur,
    pour pouvoir les rattacher à son compte si elle se connecte ou crée un compte ensuite."""
    ids = list(request.session.get(GUEST_ORDERS_KEY, []))
    ids.append(order.pk)
    request.session[GUEST_ORDERS_KEY] = ids


def claim_guest_orders(request):
    """À appeler juste après une connexion / inscription : rattache au compte les commandes
    passées en invitée depuis ce même navigateur (jamais celles d'une autre personne)."""
    ids = request.session.pop(GUEST_ORDERS_KEY, [])
    if ids and request.user.is_authenticated:
        Order.objects.filter(pk__in=ids, user__isnull=True).update(user=request.user)
