from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from cart.utils import merge_guest_cart
from orders.utils import claim_guest_orders
from .forms import SignUpForm, AddressForm, ProfileInfoForm, AjaLoginForm
from .models import Address


class AjaLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AjaLoginForm

    def form_valid(self, form):
        # La session change à la connexion : on garde le panier commencé en tant qu'invitée.
        old_key = self.request.session.session_key
        response = super().form_valid(form)
        merge_guest_cart(self.request, old_key)
        claim_guest_orders(self.request)
        return response


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            old_key = request.session.session_key
            login(request, user)
            merge_guest_cart(request, old_key)
            claim_guest_orders(request)
            messages.success(request, f"Bienvenue chez AJA LEY, {user.first_name} !")
            return redirect("accounts:profile")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile(request):
    """Mon compte : page d'accueil simple (Mes commandes / Mes informations / Se déconnecter)."""
    return render(request, "accounts/profile.html")


@login_required
def info(request):
    """Mes informations : nom, email, téléphone + adresses déjà enregistrées."""
    if request.method == "POST":
        form = ProfileInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour.")
            return redirect("accounts:info")
    else:
        form = ProfileInfoForm(instance=request.user)
    addresses = Address.objects.filter(user=request.user)
    return render(request, "accounts/info.html", {"form": form, "addresses": addresses})


@login_required
def address_add(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Adresse enregistrée.")
            return redirect("accounts:info")
    else:
        form = AddressForm()
    return render(request, "accounts/address_form.html", {"form": form})
