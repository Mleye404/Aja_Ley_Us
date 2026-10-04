from django.db import migrations, models

# Tarifs par ville qui étaient créés par l'ancien seed_ajaley. Ils contredisent la règle actuelle
# (Thiès 1 000 FCFA / toutes les autres régions 2 000 FCFA) : on les retire uniquement s'ils ont
# encore exactement leur valeur d'origine (un tarif modifié à la main est conservé).
OLD_SEEDED_RATES = [("Mbour", 3000), ("Saint-Louis", 3500), ("Kaolack", 3500), ("Ziguinchor", 4000)]


def remove_old_seeded_rates(apps, schema_editor):
    ShippingRate = apps.get_model("orders", "ShippingRate")
    for city, fee in OLD_SEEDED_RATES:
        ShippingRate.objects.filter(city=city, fee=fee).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_number_status_delivery'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='city',
            field=models.CharField(max_length=100, verbose_name='Région / ville'),
        ),
        migrations.AlterField(
            model_name='shippingrate',
            name='city',
            field=models.CharField(help_text='Facultatif : remplace le tarif par défaut pour cette région (par défaut : Thiès 1 000 FCFA, autres régions 2 000 FCFA).', max_length=100, unique=True, verbose_name='Région'),
        ),
        migrations.RunPython(remove_old_seeded_rates, migrations.RunPython.noop),
    ]
