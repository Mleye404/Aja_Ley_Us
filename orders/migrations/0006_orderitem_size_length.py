from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_delivery_zone_locality'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='size',
            field=models.CharField(blank=True, max_length=10, verbose_name='Taille'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='length',
            field=models.CharField(blank=True, max_length=10, verbose_name='Longueur'),
        ),
    ]
