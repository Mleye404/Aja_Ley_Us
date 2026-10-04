from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("Téléphone", max_length=30, blank=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"

    def __str__(self):
        return f"Profil de {self.user}"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              null=True, blank=True, related_name="addresses")
    first_name = models.CharField("Prénom", max_length=80)
    last_name = models.CharField("Nom", max_length=80)
    phone = models.CharField("Téléphone", max_length=30)
    email = models.EmailField("Email", blank=True)
    country = models.CharField("Pays", max_length=100, default="Sénégal")
    city = models.CharField("Ville", max_length=100)
    district = models.CharField("Quartier", max_length=100, blank=True)
    full_address = models.TextField("Adresse complète")
    postal_code = models.CharField("Code postal", max_length=20, blank=True)
    extra_info = models.CharField("Indication complémentaire", max_length=255, blank=True)
    is_default = models.BooleanField("Adresse par défaut", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"

    def __str__(self):
        return f"{self.full_address}, {self.city} ({self.country})"
