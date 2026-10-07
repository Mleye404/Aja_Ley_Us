from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django import forms

from orders.models import Order
from products.models import Product


class StaffAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Identifiant ou mot de passe incorrect, ou accès non autorisé.",
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")


class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("status", "expected_delivery_date")
        widgets = {"expected_delivery_date": forms.DateInput(attrs={"type": "date"})}


class ProductForm(forms.ModelForm):
    photo = forms.ImageField(label="Photo principale", required=False)

    class Meta:
        model = Product
        fields = (
            "name", "category", "description", "price", "color", "is_available",
            "is_featured", "is_new", "is_bestseller", "promo_active", "promo_price",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}