import secrets
import string
from urllib.parse import quote
from django.db import models
from django.conf import settings
from products.models import Product
from .constants import is_senegal


def generate_order_reference():
    # Référence aléatoire : elle sert de lien privé pour la page de confirmation d'une commande invitée.
    alphabet = string.ascii_uppercase + string.digits
    return "AJA-" + "".join(secrets.choice(alphabet) for _ in range(10))


def format_fcfa(amount):
    return f"{amount:,}".replace(",", " ")


def format_cm(value):
    """Affiche 92 au lieu de 92.0, mais garde 92.5 si la mesure n'est pas ronde."""
    if value is None:
        return ""
    value = float(value)
    return f"{value:g}"


class ShippingRate(models.Model):
    """Frais de livraison administrables depuis Django Admin."""
    city = models.CharField("Région", max_length=100, unique=True,
                            help_text="Facultatif : remplace le tarif par défaut (2 000 FCFA) d'une région sans zones "
                                      "de livraison. Dakar et Thiès utilisent leurs zones.")
    fee = models.PositiveIntegerField("Frais (FCFA)")

    class Meta:
        verbose_name = "Frais de livraison"
        verbose_name_plural = "Frais de livraison"

    def __str__(self):
        return f"{self.city} — {self.fee} FCFA"


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PREPARING = "preparing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_CONFIRMED, "Confirmée"),
        (STATUS_PREPARING, "En préparation"),
        (STATUS_SHIPPED, "Expédiée"),
        (STATUS_DELIVERED, "Livrée"),
        (STATUS_CANCELLED, "Annulée"),
    ]

    # Statuts « terminés » : la commande disparaît de la liste « Mes commandes » de la cliente
    # (elle reste enregistrée et visible dans l'administration).
    FINAL_STATUSES = [STATUS_DELIVERED, STATUS_CANCELLED]

    # Étapes affichées dans le suivi visuel (une commande annulée n'a pas de suivi).
    TRACKING_STEPS = [
        (STATUS_PENDING, "Commande reçue"),
        (STATUS_CONFIRMED, "Commande confirmée"),
        (STATUS_PREPARING, "En préparation"),
        (STATUS_SHIPPED, "Expédiée"),
        (STATUS_DELIVERED, "Livrée"),
    ]

    reference = models.CharField(max_length=20, unique=True, default=generate_order_reference)
    # Numéro lisible généré à l'enregistrement : AJL-00042 (affiché « #AJL-00042 »)
    number = models.CharField("Numéro de commande", max_length=20, unique=True, null=True, blank=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    # Informations cliente (toujours renseignées, même en invitée)
    first_name = models.CharField("Prénom", max_length=80)
    last_name = models.CharField("Nom", max_length=80)
    phone = models.CharField("Téléphone", max_length=30)
    email = models.EmailField("Email", blank=True)

    # Livraison : pays, région (ou ville à l'international), zone, localité, quartier. Pas d'adresse complète.
    country = models.CharField("Pays", max_length=100, default="Sénégal")
    # Sénégal : contient la RÉGION choisie dans la liste ; international : la ville.
    city = models.CharField("Région / ville", max_length=100)
    # Zone de livraison (Dakar / Thiès) et localité (banlieue, autre localité de Thiès)
    delivery_zone = models.CharField("Zone de livraison", max_length=60, blank=True)
    locality = models.CharField("Ville / localité", max_length=100, blank=True)
    district = models.CharField("Quartier", max_length=100, blank=True)
    full_address = models.TextField("Adresse complète", blank=True)
    postal_code = models.CharField("Code postal", max_length=20, blank=True)
    extra_info = models.CharField("Instructions de livraison", max_length=255, blank=True)

    shipping_fee = models.PositiveIntegerField("Frais de livraison (FCFA)", default=0)
    shipping_note = models.CharField("Note livraison", max_length=255, blank=True)
    subtotal = models.PositiveIntegerField("Sous-total (FCFA)", default=0)
    total = models.PositiveIntegerField("Total (FCFA)", default=0)

    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expected_delivery_date = models.DateField("Date de livraison prévue", null=True, blank=True,
                                              help_text="Laisser vide : « à confirmer » est affiché à la cliente.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande {self.display_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f"AJL-{self.pk:05d}"
            type(self).objects.filter(pk=self.pk).update(number=self.number)

    @property
    def display_number(self):
        return f"#{self.number}" if self.number else self.reference

    @property
    def is_cancelled(self):
        return self.status == self.STATUS_CANCELLED

    @property
    def tracking_steps(self):
        """Progression pour le suivi visuel : [{"label", "state"}], state = done / current / todo."""
        if self.is_cancelled:
            return []
        keys = [k for k, _ in self.TRACKING_STEPS]
        current = keys.index(self.status)
        steps = []
        for i, (_, label) in enumerate(self.TRACKING_STEPS):
            if i == 0 or i < current or self.status == self.STATUS_DELIVERED:
                state = "done"       # « Commande reçue » est toujours validée
            elif i == current:
                state = "current"
            else:
                state = "todo"
            steps.append({"label": label, "state": state})
        return steps

    @property
    def is_international(self):
        return not is_senegal(self.country)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def whatsapp_phone(self):
        """Numéro WhatsApp approprié selon le pays de la cliente."""
        phone = settings.WHATSAPP_INTL if self.is_international else settings.WHATSAPP_SENEGAL
        return phone.replace("+", "").replace(" ", "")

    @property
    def whatsapp_message(self):
        """Message WhatsApp généré automatiquement à partir des données réelles de la commande
        (adapté au Sénégal ou à l'international)."""
        intl = self.is_international
        if intl:
            lines = [
                "Bonjour AJA LEY,",
                "",
                f"Je souhaite confirmer ma commande internationale {self.display_number}.",
                "",
                f"Nom : {self.first_name} {self.last_name}",
                f"Téléphone : {self.phone}",
            ]
        else:
            lines = [
                "Bonjour AJA LEY 👋",
                "",
                f"Je souhaite passer la commande {self.display_number}.",
                "",
                "CLIENTE",
                f"Prénom : {self.first_name}",
                f"Nom : {self.last_name}",
                f"Téléphone : {self.phone}",
            ]
        if self.email:
            lines.append(f"Email : {self.email}")
        if intl:
            lines += [f"Pays : {self.country}", f"Ville : {self.city}"]
            if self.district:
                lines.append(f"Zone : {self.district}")
        else:
            lines += [f"Pays : {self.country}", f"Région : {self.city}"]
            if self.delivery_zone:
                lines.append(f"Zone de livraison : {self.delivery_zone}")
            if self.locality:
                lines.append(f"Ville / localité : {self.locality}")
            if self.district:
                lines.append(f"Quartier : {self.district}")
        lines += ["", "COMMANDE", ""]

        for item in self.items.all():
            lines.append(f"• {item.product_name} ×{item.quantity} — {format_fcfa(item.line_total)} FCFA")
            if item.size:
                lines.append(f"  Taille : {item.size}")
            if item.length:
                lines.append(f"  Longueur : {item.length}")
            measurements = []              # anciennes commandes (avant le système de tailles)
            if item.bust:
                measurements.append(f"Poitrine : {format_cm(item.bust)} cm")
            if item.waist:
                measurements.append(f"Taille : {format_cm(item.waist)} cm")
            if item.hips:
                measurements.append(f"Hanches : {format_cm(item.hips)} cm")
            if item.shoulders:
                measurements.append(f"Épaules : {format_cm(item.shoulders)} cm")
            if item.desired_length:
                measurements.append(f"Longueur souhaitée : {format_cm(item.desired_length)} cm")
            if item.sleeve_length:
                measurements.append(f"Longueur manches : {format_cm(item.sleeve_length)} cm")
            if measurements:
                lines.append("  Mensurations :")
                for m in measurements:
                    lines.append(f"  {m}")
            if item.extra_notes:
                lines.append(f"  Précisions : {item.extra_notes}")
            lines.append("")

        if intl:
            lines += [f"Montant : {format_fcfa(self.subtotal)} FCFA",
                      "Livraison internationale : À CONFIRMER"]
        else:
            lines.append(f"Sous-total : {format_fcfa(self.subtotal)} FCFA")
            if self.shipping_fee:
                lines.append(f"Livraison : {format_fcfa(self.shipping_fee)} FCFA")
            elif self.shipping_note:
                lines.append(f"Livraison : {self.shipping_note}")
            lines.append(f"TOTAL : {format_fcfa(self.total)} FCFA")

        if self.extra_info:
            lines += ["", "Instructions :", self.extra_info]

        if intl:
            lines += ["", "Je souhaite connaître les frais de livraison et finaliser ma commande."]
        else:
            lines += ["", "Merci de confirmer ma commande et le montant final à payer."]
        return "\n".join(lines)

    @property
    def whatsapp_url(self):
        return f"https://wa.me/{self.whatsapp_phone}?text={quote(self.whatsapp_message)}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    product_name = models.CharField(max_length=150)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    # Taille et longueur choisies (figées au moment de la commande)
    size = models.CharField("Taille", max_length=10, blank=True)
    length = models.CharField("Longueur", max_length=10, blank=True)

    # Anciennes mensurations (commandes passées avant le système de tailles)
    bust = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    waist = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    shoulders = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    desired_length = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    sleeve_length = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    extra_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
