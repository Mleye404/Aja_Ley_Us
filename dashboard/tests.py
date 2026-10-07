from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from orders.models import Order
from products.models import Product
from orders.models import OrderItem


class DashboardAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(username="manager", password="Strong-test-pass-482", is_staff=True)
        self.customer = user_model.objects.create_user(username="customer", password="Strong-test-pass-482")

    def test_guest_is_sent_to_admin_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("dashboard:login")))

    def test_customer_cannot_enter_admin_dashboard(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("dashboard:login")))

    def test_customer_cannot_login_to_admin_area(self):
        response = self.client.post(reverse("dashboard:login"), {
            "username": self.customer.username,
            "password": "Strong-test-pass-482",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_can_login_to_admin_area(self):
        response = self.client.post(reverse("dashboard:login"), {
            "username": self.staff.username,
            "password": "Strong-test-pass-482",
        })
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_admin_logout_returns_to_admin_login(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:logout"))
        self.assertRedirects(response, reverse("dashboard:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_can_update_order_status_and_delivery_date(self):
        order = Order.objects.create(first_name="Awa", last_name="Ndiaye", phone="770000000", city="Dakar")
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:order_update", args=[order.pk]), {
            "status": Order.STATUS_CONFIRMED,
            "expected_delivery_date": "2026-10-20",
        })
        self.assertRedirects(response, reverse("dashboard:order_update", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CONFIRMED)
        self.assertEqual(order.expected_delivery_date.isoformat(), "2026-10-20")

    def test_staff_can_create_product_with_promotion(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:product_create"), {
            "name": "Robe test",
            "description": "Fiche de test",
            "price": 18000,
            "color": "Noir",
            "is_available": "on",
            "promo_active": "on",
            "promo_price": 15000,
        })
        self.assertRedirects(response, reverse("dashboard:products"))
        product = Product.objects.get(name="Robe test")
        self.assertEqual(product.current_price, 15000)

    def test_product_delete_requires_confirmation_and_preserves_order_snapshot(self):
        product = Product.objects.create(name="Robe archive", price=22000)
        order = Order.objects.create(first_name="Awa", last_name="Ndiaye", phone="770000000", city="Dakar")
        order_item = OrderItem.objects.create(
            order=order, product=product, product_name=product.name, unit_price=product.price,
        )
        self.client.force_login(self.staff)

        confirmation = self.client.get(reverse("dashboard:product_delete", args=[product.pk]))
        self.assertEqual(confirmation.status_code, 200)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

        response = self.client.post(reverse("dashboard:product_delete", args=[product.pk]))
        self.assertRedirects(response, reverse("dashboard:products"))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        order_item.refresh_from_db()
        self.assertIsNone(order_item.product)
        self.assertEqual(order_item.product_name, "Robe archive")

    def test_marking_product_unavailable_preserves_product_and_order_history(self):
        product = Product.objects.create(name="Robe à retirer", price=22000)
        order = Order.objects.create(first_name="Awa", last_name="Ndiaye", phone="770000000", city="Dakar")
        order_item = OrderItem.objects.create(
            order=order, product=product, product_name=product.name, unit_price=product.price,
        )
        self.client.force_login(self.staff)

        response = self.client.post(reverse("dashboard:product_toggle_availability", args=[product.pk]))

        self.assertRedirects(response, reverse("dashboard:products"))
        product.refresh_from_db()
        order_item.refresh_from_db()
        self.assertFalse(product.is_available)
        self.assertEqual(order_item.product, product)
        self.assertEqual(order_item.product_name, "Robe à retirer")