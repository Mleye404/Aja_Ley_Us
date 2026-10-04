from django.db import migrations, models

# Anciens statuts -> nouveaux statuts
FORWARD = {
    "pending_payment": "pending",
    "paid": "confirmed",
    "confirmed": "confirmed",
    "preparing": "preparing",
    "ready": "preparing",
    "shipping": "shipped",
    "delivered": "delivered",
    "cancelled": "cancelled",
}
BACKWARD = {
    "pending": "pending_payment",
    "confirmed": "confirmed",
    "preparing": "preparing",
    "shipped": "shipping",
    "delivered": "delivered",
    "cancelled": "cancelled",
}


def migrate_orders(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.all():
        order.status = FORWARD.get(order.status, "pending")
        if not order.number:
            order.number = f"AJL-{order.pk:05d}"
        order.save(update_fields=["status", "number"])


def unmigrate_orders(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    for order in Order.objects.all():
        order.status = BACKWARD.get(order.status, "pending_payment")
        order.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_order_extra_info_alter_order_full_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='number',
            field=models.CharField(blank=True, editable=False, max_length=20, null=True, unique=True, verbose_name='Numéro de commande'),
        ),
        migrations.AddField(
            model_name='order',
            name='expected_delivery_date',
            field=models.DateField(blank=True, help_text='Laisser vide : « à confirmer » est affiché à la cliente.', null=True, verbose_name='Date de livraison prévue'),
        ),
        migrations.RunPython(migrate_orders, unmigrate_orders),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'En attente'), ('confirmed', 'Confirmée'), ('preparing', 'En préparation'), ('shipped', 'Expédiée'), ('delivered', 'Livrée'), ('cancelled', 'Annulée')], default='pending', max_length=20, verbose_name='Statut'),
        ),
    ]
