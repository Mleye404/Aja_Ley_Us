from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_regions_and_shipping'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_zone',
            field=models.CharField(blank=True, max_length=60, verbose_name='Zone de livraison'),
        ),
        migrations.AddField(
            model_name='order',
            name='locality',
            field=models.CharField(blank=True, max_length=100, verbose_name='Ville / localité'),
        ),
        migrations.AlterField(
            model_name='shippingrate',
            name='city',
            field=models.CharField(help_text="Facultatif : remplace le tarif par défaut (2 000 FCFA) d'une région sans zones de livraison. Dakar et Thiès utilisent leurs zones.", max_length=100, unique=True, verbose_name='Région'),
        ),
    ]
