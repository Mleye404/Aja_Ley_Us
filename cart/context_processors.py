from .models import Cart


def cart_context(request):
    """Nombre d'articles du panier pour l'en-tête (ne crée jamais de panier)."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, is_ordered=False).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key, user=None, is_ordered=False).first() if session_key else None
    return {"cart_items_count": cart.total_items if cart else 0}
