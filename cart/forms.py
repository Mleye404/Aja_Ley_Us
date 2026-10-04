from django import forms

from .sizes import LENGTHS, SIZES


class SizeForm(forms.Form):
    """Choix de la taille (XS à XXL) et de la longueur — plus aucune saisie de mensurations."""
    size = forms.ChoiceField(
        label="Taille", choices=[(s, s) for s in SIZES],
        error_messages={"required": "Veuillez choisir votre taille.",
                        "invalid_choice": "Veuillez choisir une taille dans la liste."},
    )
    length = forms.ChoiceField(
        label="Longueur", choices=[("", "Choisissez votre longueur")] + [(l, l) for l in LENGTHS],
        error_messages={"required": "Veuillez choisir votre longueur.",
                        "invalid_choice": "Veuillez choisir une longueur dans la liste."},
    )
