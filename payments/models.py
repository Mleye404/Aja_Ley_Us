import random
import string
from django.db import models
from orders.models import Order


def generate_payment_reference():
    return "PAY-" + "".join(random.choices(string.digits, k=10))


class Payment(models.Model):
    METHOD_CHOICES = [
        ("WAVE", "Wave"),
        ("ORANGE_MONEY", "Orange Money"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "En attente"),
        ("PAID", "Payé"),
        ("FAILED", "Échoué"),
        ("CANCELLED", "Annulé"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    reference = models.CharField(max_length=30, unique=True, default=generate_payment_reference)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"{self.reference} — {self.get_method_display()} — {self.get_status_display()}"
