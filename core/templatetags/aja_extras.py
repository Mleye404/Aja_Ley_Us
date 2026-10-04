from django import template

register = template.Library()


@register.filter
def fcfa(value):
    """15000 -> « 15 000 » (espace insécable, pour éviter les retours à la ligne)."""
    try:
        return f"{int(value):,}".replace(",", "\u00a0")
    except (TypeError, ValueError):
        return value
