from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("choisir/<str:reference>/", views.choose_method, name="choose"),
    path("simuler/<str:reference>/", views.simulate, name="simulate"),
]
