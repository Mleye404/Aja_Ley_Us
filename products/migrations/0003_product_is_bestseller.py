from django.db import migrations, models

# Sélection initiale des « meilleures ventes » parmi les anciens modèles disponibles
# (modifiable ensuite dans l'admin : case « Meilleure vente »).
INITIAL_BESTSELLERS = ["Aita Dress", "Pamela Set", "Rokhaya Set", "Baaly Dress"]


def mark_initial_bestsellers(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    if not Product.objects.filter(is_bestseller=True).exists():
        Product.objects.filter(name__in=INITIAL_BESTSELLERS, is_available=True).update(is_bestseller=True)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_product_promo'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_bestseller',
            field=models.BooleanField(default=False, help_text="Affiché dans « Nos meilleures ventes » sur la page d'accueil.", verbose_name='Meilleure vente'),
        ),
        migrations.RunPython(mark_initial_bestsellers, migrations.RunPython.noop),
    ]
