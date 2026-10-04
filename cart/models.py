from django.db import models
from django.conf import settings
from products.models import Product


class Cart(models.Model):
    """Un panier est lié soit à un utilisateur connecté, soit à une session (cliente invitée)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              null=True, blank=True, related_name="carts")
    session_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_ordered = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def __str__(self):
        return f"Panier #{self.pk}"

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    # Taille et longueur choisies sur la fiche produit pour CET article du panier
    size = models.CharField("Taille", max_length=10, blank=True)
    length = models.CharField("Longueur", max_length=10, blank=True)

    # Anciennes mensurations (plus demandées ; conservées pour les paniers / commandes existants)
    bust = models.DecimalField("Tour de poitrine (cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    waist = models.DecimalField("Tour de taille (cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    hips = models.DecimalField("Tour de hanches (cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    shoulders = models.DecimalField("Largeur des épaules (cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    desired_length = models.DecimalField("Longueur souhaitée (cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    sleeve_length = models.DecimalField("Longueur des manches (cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    extra_notes = models.TextField("Informations complémentaires", blank=True)

    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.product.current_price * self.quantity

    @property
    def has_size(self):
        return bool(self.size or self.length)

    @property
    def has_measurements(self):
        return any([self.bust, self.waist, self.hips, self.shoulders, self.desired_length, self.sleeve_length])
