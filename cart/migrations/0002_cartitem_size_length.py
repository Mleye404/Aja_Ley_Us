from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='size',
            field=models.CharField(blank=True, max_length=10, verbose_name='Taille'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='length',
            field=models.CharField(blank=True, max_length=10, verbose_name='Longueur'),
        ),
    ]
