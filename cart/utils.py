from .models import Cart


def get_or_create_cart(request):
    """Retourne le panier courant : lié à l'utilisateur s'il est connecté,
    sinon lié à la session du navigateur (cliente invitée)."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, is_ordered=False)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None, is_ordered=False)
    return cart


def merge_guest_cart(request, old_session_key):
    """À appeler juste après une connexion / inscription : reporte dans le panier de la
    cliente les articles ajoutés en tant qu'invitée (la session change au login)."""
    if not old_session_key or not request.user.is_authenticated:
        return
    guest_cart = Cart.objects.filter(session_key=old_session_key, user=None, is_ordered=False).first()
    if not guest_cart or not guest_cart.items.exists():
        return
    user_cart, _ = Cart.objects.get_or_create(user=request.user, is_ordered=False)
    for item in guest_cart.items.all():
        existing = user_cart.items.filter(product=item.product, size=item.size, length=item.length).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
            item.delete()
        else:
            item.cart = user_cart
            item.save()
    guest_cart.delete()
