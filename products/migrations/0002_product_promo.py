from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.PositiveIntegerField(verbose_name='Prix normal (FCFA)'),
        ),
        migrations.AddField(
            model_name='product',
            name='promo_active',
            field=models.BooleanField(default=False, verbose_name='Promotion activée'),
        ),
        migrations.AddField(
            model_name='product',
            name='promo_price',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Prix promotionnel (FCFA)'),
        ),
    ]
