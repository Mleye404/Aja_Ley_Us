from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, F, IntegerField, Q, When
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField("Slug", unique=True, blank=True)
    description = models.TextField("Description", blank=True)
    image = models.ImageField("Image", upload_to="categories/", blank=True, null=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# Un produit est « en promotion » quand la promotion est activée, que le prix
# promotionnel est valide (0 < prix promo < prix normal) ET que le produit est
# disponible : un produit en rupture reste visible mais n'est jamais commandable,
# même s'il garde un ancien prix promotionnel.
PROMO_Q = Q(is_available=True, promo_active=True, promo_price__gt=0, promo_price__lt=F("price"))


class ProductQuerySet(models.QuerySet):
    def on_promo(self):
        """Produits actuellement en promotion."""
        return self.filter(PROMO_Q)

    def with_effective_price(self):
        """Ajoute `effective_price` : prix promo si promotion en cours, sinon prix normal."""
        return self.annotate(effective_price=Case(
            When(PROMO_Q, then=F("promo_price")),
            default=F("price"),
            output_field=IntegerField(),
        ))


class Product(models.Model):
    name = models.CharField("Nom", max_length=150)
    slug = models.SlugField("Slug", unique=True, blank=True)
    category = models.ForeignKey(Category, verbose_name="Catégorie", on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="products")
    description = models.TextField("Description", blank=True)
    price = models.PositiveIntegerField("Prix normal (FCFA)")
    is_bestseller = models.BooleanField("Meilleure vente", default=False,
                                        help_text="Affiché dans « Nos meilleures ventes » sur la page d'accueil.")
    promo_active = models.BooleanField("Promotion activée", default=False)
    promo_price = models.PositiveIntegerField("Prix promotionnel (FCFA)", null=True, blank=True)
    color = models.CharField("Couleur", max_length=100, blank=True)
    is_available = models.BooleanField("Disponible", default=True)
    is_featured = models.BooleanField("Mis en avant", default=False)
    is_new = models.BooleanField("Nouveau", default=False)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.promo_active:
            if not self.promo_price:
                raise ValidationError({"promo_price": "Indiquez un prix promotionnel pour activer la promotion."})
            if self.price is not None and self.promo_price >= self.price:
                raise ValidationError({"promo_price": "Le prix promotionnel doit être inférieur au prix normal."})

    @property
    def is_on_promo(self):
        return bool(
            self.is_available and self.promo_active
            and self.promo_price and self.promo_price < self.price
        )

    @property
    def current_price(self):
        """Prix réellement payé : prix promotionnel si la promotion est en cours, sinon prix normal.
        C'est ce prix qui est utilisé dans le panier, la commande et le message WhatsApp."""
        return self.promo_price if self.is_on_promo else self.price

    @property
    def discount_percent(self):
        """Pourcentage de réduction calculé automatiquement (arrondi à l'entier le plus proche)."""
        if not self.is_on_promo:
            return 0
        return (200 * (self.price - self.promo_price) + self.price) // (2 * self.price)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:detail", args=[self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Photo", upload_to="products/")
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Photo produit"
        verbose_name_plural = "Photos produit"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product.name} - photo {self.order + 1}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} ♥ {self.product}"
