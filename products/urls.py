from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("favoris/", views.favorites_list, name="favorites"),
    path("favoris/<slug:slug>/", views.toggle_favorite, name="toggle_favorite"),
    path("<slug:slug>/", views.detail, name="detail"),
]
