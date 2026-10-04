import re

from django import forms

from .constants import COUNTRIES, DELIVERY_ZONES, OTHER_LOCALITY, SENEGAL_REGIONS, zones_for


class CheckoutForm(forms.Form):
    """Commande au Sénégal : la cliente choisit sa région dans une liste (pas de saisie libre)."""
    first_name = forms.CharField(label="Prénom", max_length=80)
    last_name = forms.CharField(label="Nom", max_length=80)
    phone = forms.CharField(label="Numéro de téléphone", max_length=30)
    email = forms.EmailField(label="Email (optionnel)", required=False)

    region = forms.ChoiceField(
        label="Région",
        choices=[("", "Sélectionnez votre région")] + [(r, r) for r in SENEGAL_REGIONS],
        error_messages={"required": "Veuillez sélectionner votre région.",
                        "invalid_choice": "Veuillez sélectionner une région dans la liste."},
    )
    # Zone de livraison AJA LEY : uniquement pour Dakar et Thiès (voir constants.DELIVERY_ZONES).
    delivery_zone = forms.ChoiceField(
        label="Zone de livraison", required=False,
        choices=[("", "Choisissez votre zone")] + [(z["name"], z["name"]) for zs in DELIVERY_ZONES.values() for z in zs],
        error_messages={"invalid_choice": "Veuillez choisir une zone de livraison dans la liste."},
    )
    # Ville / localité : liste proposée selon la zone (Thiès « autre localité », banlieue dakaroise) ;
    # « Autre » ouvre un champ pour préciser. Le quartier ne modifie jamais le tarif.
    locality = forms.ChoiceField(
        label="Ville / localité", required=False,
        choices=[("", "Choisissez votre ville / localité")] + [
            (l, l) for l in dict.fromkeys(l for zs in DELIVERY_ZONES.values() for z in zs for l in z["localities"])],
        error_messages={"invalid_choice": "Veuillez choisir votre ville / localité dans la liste."},
    )
    locality_other = forms.CharField(label="Précisez votre ville / localité", max_length=100, required=False)
    district = forms.CharField(label="Quartier", max_length=100, required=False)
    extra_info = forms.CharField(
        label="Instructions de livraison (optionnel)",
        max_length=255, required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def clean(self):
        cleaned = super().clean()
        region = cleaned.get("region")
        if not region or "delivery_zone" in self.errors:
            return cleaned
        zones = zones_for(region)
        if not zones:                      # autres régions : tarif unique, pas de zone
            cleaned["delivery_zone"] = ""
            cleaned["locality"] = ""
            return cleaned
        zone = next((z for z in zones if z["name"] == cleaned.get("delivery_zone")), None)
        if not zone:
            self.add_error("delivery_zone", "Veuillez choisir votre zone de livraison.")
        elif zone["locality"]:
            if "locality" in self.errors:
                return cleaned
            locality = cleaned.get("locality") or ""
            if locality not in zone["localities"]:
                self.add_error("locality", "Veuillez choisir votre ville / localité.")
            elif locality == OTHER_LOCALITY:
                other = (cleaned.get("locality_other") or "").strip()
                if other:
                    cleaned["locality"] = other
                else:
                    self.add_error("locality_other", "Précisez votre ville / localité.")
        else:
            cleaned["locality"] = ""
            cleaned["locality_other"] = ""
        return cleaned


class InternationalCheckoutForm(forms.Form):
    """Commande depuis l'étranger : pas d'adresse complète, frais de livraison à confirmer."""
    first_name = forms.CharField(label="Prénom", max_length=80)
    last_name = forms.CharField(label="Nom", max_length=80)
    phone = forms.CharField(
        label="Téléphone (avec indicatif international)", max_length=30,
        widget=forms.TextInput(attrs={"placeholder": "+33 6 12 34 56 78", "type": "tel"}),
    )
    email = forms.EmailField(label="Email (optionnel)", required=False)

    country = forms.ChoiceField(
        label="Pays",
        choices=[("", "Sélectionnez votre pays")] + [(c, c) for c in COUNTRIES],
        error_messages={"required": "Veuillez sélectionner votre pays.",
                        "invalid_choice": "Veuillez sélectionner un pays dans la liste."},
    )
    city = forms.CharField(label="Ville", max_length=100)
    district = forms.CharField(label="Quartier / zone (si pertinent)", max_length=100, required=False)
    extra_info = forms.CharField(
        label="Instructions de livraison (optionnel)",
        max_length=255, required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def clean_phone(self):
        phone = " ".join(self.cleaned_data["phone"].split())
        digits = re.sub(r"\D", "", phone)
        if not phone.startswith("+") or not 8 <= len(digits) <= 15:
            raise forms.ValidationError(
                "Indiquez le numéro avec l'indicatif international, par exemple +33 6 12 34 56 78.")
        return phone
