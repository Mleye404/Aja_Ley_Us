from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/international/", views.checkout_international, name="checkout_international"),
    path("recapitulatif/", views.recap, name="recap"),
    path("mes-commandes/", views.my_orders, name="my_orders"),
    path("mes-commandes/<str:number>/", views.order_detail, name="order_detail"),
    path("confirmation/<str:reference>/", views.confirmation, name="confirmation"),
]
