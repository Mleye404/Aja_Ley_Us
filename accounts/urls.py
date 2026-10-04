from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("connexion/", views.AjaLoginView.as_view(), name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("inscription/", views.signup, name="signup"),
    path("profil/", views.profile, name="profile"),
    path("profil/informations/", views.info, name="info"),
    path("profil/adresse/ajouter/", views.address_add, name="address_add"),
]
