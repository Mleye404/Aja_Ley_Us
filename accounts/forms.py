from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Address, Profile


class AjaLoginForm(AuthenticationForm):
    """Connexion : messages d'erreur clairs en français.
    On ne précise pas si c'est le nom d'utilisateur OU le mot de passe qui est faux
    (bonne pratique de sécurité : cela évite de révéler quels comptes existent)."""
    error_messages = {
        "invalid_login": "Nom d'utilisateur ou mot de passe incorrect. Vérifiez vos informations et réessayez.",
        "inactive": "Ce compte est désactivé. Contactez AJA LEY sur WhatsApp.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nom d'utilisateur"


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=True, label="Prénom")
    last_name = forms.CharField(required=False, label="Nom")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "password1", "password2"]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ["user", "is_default", "created_at"]
        widgets = {
            "full_address": forms.Textarea(attrs={"rows": 2}),
        }


class ProfileInfoForm(forms.ModelForm):
    """« Mes informations » : nom, email, téléphone."""
    phone = forms.CharField(label="Téléphone", max_length=30, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "Prénom", "last_name": "Nom", "email": "Email"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        profile = getattr(self.instance, "profile", None)
        if profile:
            self.fields["phone"].initial = profile.phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get("phone", "")
            profile.save()
        return user
