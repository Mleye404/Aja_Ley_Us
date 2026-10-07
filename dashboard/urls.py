from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("connexion/", views.AdminLoginView.as_view(), name="login"),
    path("deconnexion/", views.admin_logout, name="logout"),
    path("", views.dashboard_home, name="home"),
    path("commandes/", views.order_list, name="orders"),
    path("commandes/<int:pk>/", views.order_update, name="order_update"),
    path("produits/", views.product_list, name="products"),
    path("produits/nouveau/", views.product_create, name="product_create"),
    path("produits/<int:pk>/disponibilite/", views.product_toggle_availability, name="product_toggle_availability"),
    path("produits/<int:pk>/supprimer/", views.product_delete, name="product_delete"),
    path("produits/<int:pk>/modifier/", views.product_update, name="product_update"),
]
