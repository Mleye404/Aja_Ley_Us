from datetime import date

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from urllib.parse import unquote

from accounts.models import Profile
from cart.models import Cart, CartItem
from products.models import Category, Product
from .constants import SENEGAL_REGIONS
from .models import Order, OrderItem, ShippingRate
from .views import compute_shipping

CHECKOUT = {
    "first_name": "Awa", "last_name": "Diop", "phone": "770000000", "email": "awa@example.com",
    "region": "Thiès", "delivery_zone": "Thiès-ville", "locality": "", "locality_other": "",
    "district": "Randoulène", "extra_info": "",
}
INTL_CHECKOUT = {
    "first_name": "Awa", "last_name": "Diop", "phone": "+33 6 12 34 56 78", "email": "awa@example.com",
    "country": "France", "city": "Paris", "district": "Belleville", "extra_info": "",
}
SIZE = {"size": "M", "length": "1m65"}


class OrderFlowMixin:
    def setUp(self):
        cat = Category.objects.create(name="Robes", slug="robes")
        self.dress = Product.objects.create(name="Aita Dress", price=15000, category=cat)
        self.set = Product.objects.create(name="Pamela Set", price=14000, category=cat)
        self.out = Product.objects.create(name="Amara Dress", price=33000, category=cat,
                                          is_available=False, promo_active=True, promo_price=30000)

    def add_to_cart(self, client, product):
        return client.post(reverse("cart:add_to_cart", args=[product.slug]), SIZE)

    def place_order(self, client, *products, checkout=CHECKOUT, url_name="orders:checkout"):
        for p in products:
            self.add_to_cart(client, p)
        client.post(reverse(url_name), checkout)
        resp = client.post(reverse("orders:recap"))
        self.assertEqual(resp.status_code, 302)
        return Order.objects.latest("id")


class GuestCheckoutTests(OrderFlowMixin, TestCase):
    def test_guest_can_order_without_account(self):  # 1, 14
        order = self.place_order(self.client, self.dress, self.set)
        self.assertIsNone(order.user)
        self.assertEqual(order.subtotal, 29000)
        self.assertEqual(order.shipping_fee, 1000)   # Thiès
        self.assertEqual(order.total, 30000)
        resp = self.client.get(reverse("orders:confirmation", args=[order.reference]))
        self.assertEqual(resp.status_code, 200)

    def test_order_number_generated_and_in_whatsapp(self):  # 7, 8, 13
        order = self.place_order(self.client, self.dress)
        self.assertRegex(order.number, r"^AJL-\d{5}$")
        self.assertEqual(order.display_number, f"#{order.number}")
        self.assertIn(f"Je souhaite passer la commande #{order.number}.", order.whatsapp_message)
        self.assertIn("Aita Dress ×1 — 15 000 FCFA", order.whatsapp_message)
        self.assertIn("Taille : M", order.whatsapp_message)
        self.assertIn("Longueur : 1m65", order.whatsapp_message)
        self.assertNotIn("Poitrine", order.whatsapp_message)
        self.assertNotIn("Adresse", order.whatsapp_message)
        self.assertIn("wa.me/", order.whatsapp_url)
        self.assertIn(order.number, unquote(order.whatsapp_url))

    def test_guest_cannot_see_account_pages(self):
        resp = self.client.get(reverse("orders:my_orders"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_payment_pages_are_not_reachable(self):  # 12
        order = self.place_order(self.client, self.dress)
        self.assertEqual(self.client.get(f"/paiement/choisir/{order.reference}/").status_code, 404)
        self.assertEqual(self.client.get(f"/paiement/simuler/{order.reference}/").status_code, 404)
        resp = self.client.get(reverse("orders:confirmation", args=[order.reference]))
        self.assertNotContains(resp, "Wave")
        self.assertNotContains(resp, "Orange Money")

    def test_international_delivery_fee_is_not_invented(self):  # 14
        order = self.place_order(self.client, self.dress, checkout=INTL_CHECKOUT,
                                 url_name="orders:checkout_international")
        self.assertTrue(order.is_international)
        self.assertEqual(order.shipping_fee, 0)
        self.assertEqual(order.shipping_note, "À confirmer")
        self.assertEqual(order.total, order.subtotal)


class SenegalRegionTests(OrderFlowMixin, TestCase):
    def order_for(self, **fields):
        return self.place_order(Client(), self.dress, checkout={**CHECKOUT, **fields})

    def test_checkout_shows_region_select_with_14_regions(self):
        self.add_to_cart(self.client, self.dress)
        resp = self.client.get(reverse("orders:checkout"))
        self.assertContains(resp, "Région")
        self.assertContains(resp, "<select")
        for region in SENEGAL_REGIONS:
            self.assertContains(resp, f'<option value="{region}"')
        self.assertEqual(len(SENEGAL_REGIONS), 14)
        self.assertNotContains(resp, 'name="city"')
        self.assertContains(resp, "Commander depuis l'international")
        self.assertContains(resp, 'id="zoneGroup"')
        self.assertContains(resp, "Zone de livraison")

    def test_scenario_1_dakar_ville_is_2000(self):  # SCÉNARIO 1
        order = self.order_for(region="Dakar", delivery_zone="Dakar-ville")
        self.assertEqual((order.shipping_fee, order.total), (2000, 17000))
        self.assertEqual(order.delivery_zone, "Dakar-ville")

    def test_scenario_2_dakar_banlieue_is_4000(self):  # SCÉNARIO 2
        order = self.order_for(region="Dakar", delivery_zone="Banlieue dakaroise", locality="Keur Massar", district="Ndiarème")
        self.assertEqual((order.shipping_fee, order.total), (4000, 19000))
        self.assertEqual(order.district, "Ndiarème")          # le quartier ne change pas le tarif
        self.assertEqual(order.locality, "Keur Massar")

    def test_scenario_3_thies_ville_is_1000(self):  # SCÉNARIO 3
        order = self.order_for(region="Thiès", delivery_zone="Thiès-ville")
        self.assertEqual((order.shipping_fee, order.total), (1000, 16000))
        self.assertEqual(order.locality, "")

    def test_scenario_4_thies_autre_localite_mbour_is_2000(self):  # SCÉNARIO 4
        order = self.order_for(region="Thiès", delivery_zone="Autre localité", locality="Mbour")
        self.assertEqual((order.shipping_fee, order.total), (2000, 17000))
        self.assertEqual((order.city, order.delivery_zone, order.locality), ("Thiès", "Autre localité", "Mbour"))
        self.assertIn("Zone de livraison : Autre localité", order.whatsapp_message)
        self.assertIn("Ville / localité : Mbour", order.whatsapp_message)
        self.assertIn("Livraison : 2 000 FCFA", order.whatsapp_message)

    def test_other_regions_keep_their_flat_2000(self):
        for region in SENEGAL_REGIONS:
            if region in ("Dakar", "Thiès"):
                continue
            order = self.order_for(region=region, delivery_zone="", locality="")
            self.assertEqual((order.shipping_fee, order.total), (2000, 17000), region)
            self.assertEqual(order.delivery_zone, "")

    def test_stale_zone_is_ignored_for_regions_without_zones(self):
        order = self.order_for(region="Louga", delivery_zone="Banlieue dakaroise", locality="Rufisque")
        self.assertEqual(order.shipping_fee, 2000)
        self.assertEqual((order.delivery_zone, order.locality), ("", ""))

    def test_zone_is_required_for_dakar_and_thies(self):
        self.add_to_cart(self.client, self.dress)
        for region in ("Dakar", "Thiès"):
            resp = self.client.post(reverse("orders:checkout"), {**CHECKOUT, "region": region, "delivery_zone": ""})
            self.assertContains(resp, "choisir votre zone de livraison")
        self.assertEqual(Order.objects.count(), 0)

    def test_locality_is_required_for_autre_localite_and_banlieue(self):
        self.add_to_cart(self.client, self.dress)
        for region, zone in (("Thiès", "Autre localité"), ("Dakar", "Banlieue dakaroise")):
            resp = self.client.post(reverse("orders:checkout"),
                                    {**CHECKOUT, "region": region, "delivery_zone": zone, "locality": ""})
            self.assertContains(resp, "choisir votre ville / localité")
        self.assertEqual(Order.objects.count(), 0)

    def test_locality_lists_per_zone(self):
        from .constants import DELIVERY_ZONES
        banlieue = DELIVERY_ZONES["Dakar"][1]["localities"]
        self.assertEqual(banlieue, ["Guédiawaye", "Keur Massar", "Rufisque", "Diamniadio", "Mbao", "ZAC Mbao",
                                    "Bargny", "Sangalkam", "Autre"])
        self.assertEqual(DELIVERY_ZONES["Thiès"][1]["localities"], ["Mbour", "Tivaouane", "Joal-Fadiouth", "Autre"])
        self.add_to_cart(self.client, self.dress)
        resp = self.client.post(reverse("orders:checkout"),
                                {**CHECKOUT, "region": "Dakar", "delivery_zone": "Banlieue dakaroise", "locality": ""})
        for name in banlieue:
            self.assertContains(resp, f'<option value="{name}"')

    def test_locality_from_the_other_zone_is_rejected(self):
        self.add_to_cart(self.client, self.dress)
        resp = self.client.post(reverse("orders:checkout"), {
            **CHECKOUT, "region": "Thiès", "delivery_zone": "Autre localité", "locality": "Rufisque"})
        self.assertContains(resp, "choisir votre ville / localité")
        self.assertEqual(Order.objects.count(), 0)

    def test_autre_locality_requires_a_precision_and_is_saved(self):
        self.add_to_cart(self.client, self.dress)
        resp = self.client.post(reverse("orders:checkout"), {
            **CHECKOUT, "region": "Thiès", "delivery_zone": "Autre localité", "locality": "Autre", "locality_other": " "})
        self.assertContains(resp, "Précisez votre ville / localité")
        self.assertEqual(Order.objects.count(), 0)
        order = self.order_for(region="Thiès", delivery_zone="Autre localité", locality="Autre",
                               locality_other="Pout")
        self.assertEqual((order.locality, order.shipping_fee), ("Pout", 2000))

    def test_zone_from_the_wrong_region_is_rejected(self):
        self.add_to_cart(self.client, self.dress)
        resp = self.client.post(reverse("orders:checkout"),
                                {**CHECKOUT, "region": "Thiès", "delivery_zone": "Banlieue dakaroise", "locality": "x"})
        self.assertContains(resp, "choisir votre zone de livraison")
        self.assertEqual(Order.objects.count(), 0)

    def test_compute_shipping_rules(self):
        self.assertEqual(compute_shipping("Sénégal", "Dakar", "Dakar-ville"), (2000, ""))
        self.assertEqual(compute_shipping("Sénégal", "Dakar", "Banlieue dakaroise"), (4000, ""))
        self.assertEqual(compute_shipping("Sénégal", "Thiès", "Thiès-ville"), (1000, ""))
        self.assertEqual(compute_shipping("Sénégal", "Thiès", "Autre localité"), (2000, ""))
        self.assertEqual(compute_shipping("Sénégal", "Dakar"), (2000, ""))       # anciennes commandes
        self.assertEqual(compute_shipping("Sénégal", "Thiès"), (1000, ""))
        self.assertEqual(compute_shipping("France", "Paris"), (0, "À confirmer"))

    def test_checkout_page_exposes_config_for_dynamic_total(self):
        self.add_to_cart(self.client, self.dress)
        resp = self.client.get(reverse("orders:checkout"))
        cfg = resp.context["shipping_config"]
        self.assertEqual([z["fee"] for z in cfg["Dakar"]["zones"]], [2000, 4000])
        self.assertEqual([z["fee"] for z in cfg["Thiès"]["zones"]], [1000, 2000])
        self.assertEqual(cfg["Matam"], {"fee": 2000})
        self.assertContains(resp, 'id="shipping-config"')
        self.assertContains(resp, 'data-subtotal="15000"')
        self.assertContains(resp, "Sélectionnez votre région")

    def test_form_redisplay_keeps_zone_and_locality(self):
        self.add_to_cart(self.client, self.dress)
        resp = self.client.post(reverse("orders:checkout"),
                                {**CHECKOUT, "region": "Thiès", "delivery_zone": "Autre localité", "locality": ""})
        self.assertContains(resp, '<option value="Autre localité" selected>')
        self.assertContains(resp, '<option value="Mbour"')
        self.assertContains(resp, "Autre localité — 2")
        self.assertEqual(resp.context["shipping_fee"], 2000)
        self.assertEqual(resp.context["total"], 17000)

    def test_admin_override_for_regions_without_zones(self):
        ShippingRate.objects.create(city="Kolda", fee=2500)
        self.assertEqual(compute_shipping("Sénégal", "Kolda")[0], 2500)
        self.assertEqual(compute_shipping("Sénégal", "Louga")[0], 2000)

    def test_whatsapp_message_for_senegal(self):
        order = self.order_for(region="Dakar", delivery_zone="Banlieue dakaroise", locality="Rufisque")
        msg = order.whatsapp_message
        self.assertIn("Région : Dakar", msg)
        self.assertIn("Zone de livraison : Banlieue dakaroise", msg)
        self.assertIn("Livraison : 4 000 FCFA", msg)
        self.assertIn("TOTAL : 19 000 FCFA", msg)
        self.assertNotIn("internationale", msg)


class InternationalOrderTests(OrderFlowMixin, TestCase):
    def test_international_option_is_on_checkout_and_form_asks_country(self):  # 12, 13
        self.add_to_cart(self.client, self.dress)
        resp = self.client.get(reverse("orders:checkout_international"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="country"')
        self.assertContains(resp, 'name="city"')
        self.assertContains(resp, "indicatif international")
        self.assertContains(resp, "À confirmer")
        self.assertNotContains(resp, 'name="region"')
        self.assertNotContains(resp, "DHL")
        self.assertNotContains(resp, '<option value="Sénégal"')

    def test_country_is_required_and_phone_needs_dial_code(self):  # 13
        self.add_to_cart(self.client, self.dress)
        url = reverse("orders:checkout_international")
        resp = self.client.post(url, {**INTL_CHECKOUT, "country": ""})
        self.assertContains(resp, "sélectionner votre pays")
        resp = self.client.post(url, {**INTL_CHECKOUT, "phone": "0612345678"})
        self.assertContains(resp, "Indiquez le numéro avec l&#x27;indicatif")
        self.assertEqual(Order.objects.count(), 0)

    def test_international_flow_recap_and_order(self):  # 14
        self.add_to_cart(self.client, self.dress)
        self.client.post(reverse("orders:checkout_international"), INTL_CHECKOUT)
        recap = self.client.get(reverse("orders:recap"))
        self.assertContains(recap, "À confirmer")
        self.assertContains(recap, "Total produits")
        self.assertContains(recap, reverse("orders:checkout_international"))   # « modifier » -> bon parcours
        self.client.post(reverse("orders:recap"))
        order = Order.objects.latest("id")
        self.assertEqual((order.country, order.city, order.district), ("France", "Paris", "Belleville"))
        self.assertEqual(order.shipping_fee, 0)
        self.assertEqual(order.total, 15000)
        conf = self.client.get(reverse("orders:confirmation", args=[order.reference]))
        self.assertContains(conf, "Total produits")

    def test_international_whatsapp_message(self):  # 15, 16
        order = self.place_order(self.client, self.dress, self.set, checkout=INTL_CHECKOUT,
                                 url_name="orders:checkout_international")
        msg = order.whatsapp_message
        self.assertIn(f"Je souhaite confirmer ma commande internationale #{order.number}.", msg)
        self.assertTrue(msg.startswith("Bonjour AJA LEY,"))
        self.assertIn("Nom : Awa Diop", msg)
        self.assertIn("Téléphone : +33 6 12 34 56 78", msg)
        self.assertIn("Pays : France", msg)
        self.assertIn("Ville : Paris", msg)
        self.assertIn("Zone : Belleville", msg)
        self.assertIn("• Aita Dress ×1 — 15 000 FCFA", msg)
        self.assertIn("Montant : 29 000 FCFA", msg)
        self.assertIn("Livraison internationale : À CONFIRMER", msg)
        self.assertIn("Je souhaite connaître les frais de livraison et finaliser ma commande.", msg)
        self.assertNotIn("TOTAL :", msg)
        self.assertNotIn("DHL", msg)
        self.assertIn("wa.me/", order.whatsapp_url)       # numéro international choisi automatiquement

    def test_scenario_5_confirmation_page_has_whatsapp_button(self):  # SCÉNARIO 5
        order = self.place_order(self.client, self.dress, checkout=INTL_CHECKOUT,
                                 url_name="orders:checkout_international")
        self.assertEqual(order.shipping_fee, 0)
        self.assertEqual(order.shipping_note, "À confirmer")
        resp = self.client.get(reverse("orders:confirmation", args=[order.reference]))
        self.assertContains(resp, "Commande enregistrée !")
        self.assertContains(resp, "Pour confirmer votre commande internationale et définir les frais de livraison, "
                                  "contactez AJA LEY sur WhatsApp.")
        self.assertContains(resp, "Confirmer sur WhatsApp")
        self.assertContains(resp, "https://wa.me/13173199999?text=")
        self.assertContains(resp, "+1 317 319 9999")
        self.assertNotContains(resp, "Commander via WhatsApp")
        self.assertNotContains(resp, "wa.me/221")
        text = unquote(order.whatsapp_url.split("?text=")[1])
        self.assertIn(f"commande internationale #{order.number}", text)
        self.assertIn("Nom : Awa Diop", text)
        self.assertIn("Pays : France", text)
        self.assertIn("Montant : 15 000 FCFA", text)

    def test_national_confirmation_page_unchanged(self):
        order = self.place_order(self.client, self.dress)
        resp = self.client.get(reverse("orders:confirmation", args=[order.reference]))
        self.assertContains(resp, "Commander via WhatsApp")
        self.assertContains(resp, "https://wa.me/221776990926?text=")
        self.assertNotContains(resp, "Confirmer sur WhatsApp")

    def test_international_guest_and_logged_in(self):  # 10, 11
        guest = self.place_order(self.client, self.dress, checkout=INTL_CHECKOUT,
                                 url_name="orders:checkout_international")
        self.assertIsNone(guest.user)
        user = User.objects.create_user("awa", "awa@example.com", "pass12345", first_name="Awa")
        client = Client()
        client.login(username="awa", password="pass12345")
        order = self.place_order(client, self.dress, checkout=INTL_CHECKOUT,
                                 url_name="orders:checkout_international")
        self.assertEqual(order.user, user)
        resp = client.get(reverse("orders:my_orders"))
        self.assertContains(resp, order.display_number)
        self.assertContains(client.get(reverse("orders:order_detail", args=[order.number])), "Paris")


class PromoInOrderTests(OrderFlowMixin, TestCase):
    def test_promo_price_used_in_cart_order_and_whatsapp(self):  # 18, 19, 20
        self.dress.promo_active, self.dress.promo_price = True, 12500
        self.dress.save()
        self.add_to_cart(self.client, self.dress)
        cart_resp = self.client.get(reverse("cart:view_cart"))
        self.assertContains(cart_resp, "12\u00a0500")
        order = self.place_order(self.client)
        item = order.items.get()
        self.assertEqual(item.unit_price, 12500)
        self.assertEqual(order.subtotal, 12500)
        self.assertIn("Aita Dress ×1 — 12 500 FCFA", order.whatsapp_message)

    def test_old_orders_keep_their_price_when_promo_ends(self):
        self.dress.promo_active, self.dress.promo_price = True, 12500
        self.dress.save()
        order = self.place_order(self.client, self.dress)
        self.dress.promo_active = False
        self.dress.save()
        self.assertEqual(order.items.get().unit_price, 12500)

    def test_out_of_stock_product_cannot_be_ordered(self):  # 23
        resp = self.client.post(reverse("cart:add_to_cart", args=[self.out.slug]), SIZE)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(CartItem.objects.filter(product=self.out).exists())
        self.client.get(reverse("cart:add_to_cart", args=[self.out.slug]))
        self.assertFalse(CartItem.objects.filter(product=self.out).exists())

    def test_product_going_out_of_stock_blocks_validation(self):
        self.add_to_cart(self.client, self.dress)
        self.client.post(reverse("orders:checkout"), CHECKOUT)
        self.dress.is_available = False
        self.dress.save()
        resp = self.client.post(reverse("orders:recap"))
        self.assertRedirects(resp, reverse("cart:view_cart"))
        self.assertEqual(Order.objects.count(), 0)


class AccountOrdersTests(OrderFlowMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.awa = User.objects.create_user("awa", "awa@example.com", "pass12345", first_name="Awa")
        self.fatou = User.objects.create_user("fatou", "f@example.com", "pass12345", first_name="Fatou")
        self.staff = User.objects.create_user("khadija", "k@example.com", "pass12345", is_staff=True)

    def test_signup_creates_account(self):  # 2
        resp = self.client.post(reverse("accounts:signup"), {
            "first_name": "Mame", "last_name": "Sy", "email": "m@example.com", "username": "mame",
            "password1": "Sup3rSecret!x", "password2": "Sup3rSecret!x"})
        self.assertRedirects(resp, reverse("accounts:profile"))
        self.assertTrue(User.objects.filter(username="mame").exists())

    def test_logged_in_order_is_linked_and_listed(self):  # 3, 4, 5
        self.client.login(username="awa", password="pass12345")
        order = self.place_order(self.client, self.dress, self.set)
        self.assertEqual(order.user, self.awa)
        resp = self.client.get(reverse("orders:my_orders"))
        self.assertContains(resp, order.display_number)
        self.assertContains(resp, "Aita Dress")
        self.assertContains(resp, "Pamela Set")
        self.assertContains(resp, "30\u00a0000")

    def test_customer_cannot_see_another_customers_order(self):  # 6
        self.client.login(username="awa", password="pass12345")
        order = self.place_order(self.client, self.dress)
        self.client.logout()
        self.client.login(username="fatou", password="pass12345")
        self.assertNotContains(self.client.get(reverse("orders:my_orders")), order.number)
        self.assertEqual(self.client.get(reverse("orders:order_detail", args=[order.number])).status_code, 404)
        self.assertEqual(self.client.get(reverse("orders:confirmation", args=[order.reference])).status_code, 404)

    def test_anonymous_cannot_open_order_detail(self):  # 6
        order = Order.objects.create(user=self.awa, first_name="A", last_name="B", phone="1", city="Thiès")
        resp = self.client.get(reverse("orders:order_detail", args=[order.number]))
        self.assertEqual(resp.status_code, 302)

    def test_staff_keeps_access(self):
        order = Order.objects.create(user=self.awa, first_name="A", last_name="B", phone="1", city="Thiès")
        self.client.login(username="khadija", password="pass12345")
        self.assertEqual(self.client.get(reverse("orders:order_detail", args=[order.number])).status_code, 200)
        self.assertEqual(self.client.get(reverse("orders:confirmation", args=[order.reference])).status_code, 200)

    def test_status_and_delivery_date_visible_to_customer(self):  # 9, 10, 11
        self.client.login(username="awa", password="pass12345")
        order = self.place_order(self.client, self.dress)
        url = reverse("orders:order_detail", args=[order.number])
        self.assertContains(self.client.get(url), "à confirmer")

        order.status = Order.STATUS_PREPARING
        order.expected_delivery_date = date(2026, 10, 12)
        order.save()
        resp = self.client.get(url)
        self.assertContains(resp, "En préparation")
        self.assertContains(resp, "Livraison prévue")
        self.assertContains(resp, "12 octobre 2026")
        self.assertNotContains(resp, "à confirmer")

    def test_delivered_and_cancelled_orders_leave_my_orders(self):
        self.client.login(username="awa", password="pass12345")
        order = self.place_order(self.client, self.dress)
        url = reverse("orders:my_orders")
        self.assertContains(self.client.get(url), order.display_number)
        for status in (Order.STATUS_CONFIRMED, Order.STATUS_PREPARING, Order.STATUS_SHIPPED):
            order.status = status
            order.save()
            self.assertContains(self.client.get(url), order.display_number)
        for status in (Order.STATUS_DELIVERED, Order.STATUS_CANCELLED):
            order.status = status
            order.save()
            resp = self.client.get(url)
            self.assertNotContains(resp, order.display_number)
            self.assertContains(resp, "aucune commande en cours")
        self.assertEqual(Order.objects.filter(pk=order.pk).count(), 1)  # toujours en base / admin

    def test_order_appears_in_my_orders_right_after_validation(self):
        self.client.login(username="awa", password="pass12345")
        self.add_to_cart(self.client, self.dress)
        self.client.post(reverse("orders:checkout"), CHECKOUT)
        resp = self.client.post(reverse("orders:recap"), follow=True)
        order = Order.objects.latest("id")
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertContains(resp, "Suivre ma commande")
        self.assertContains(self.client.get(reverse("orders:my_orders")), order.display_number)

    def test_guest_order_is_claimed_after_login(self):
        order = self.place_order(self.client, self.dress)          # passée en invitée
        self.assertIsNone(order.user)
        self.client.post(reverse("accounts:login"), {"username": "awa", "password": "pass12345"})
        order.refresh_from_db()
        self.assertEqual(order.user, self.awa)
        self.assertContains(self.client.get(reverse("orders:my_orders")), order.display_number)

    def test_guest_order_is_claimed_after_signup(self):
        order = self.place_order(self.client, self.dress)
        self.client.post(reverse("accounts:signup"), {
            "first_name": "Mame", "last_name": "Sy", "email": "m@example.com", "username": "mame",
            "password1": "Sup3rSecret!x", "password2": "Sup3rSecret!x"})
        order.refresh_from_db()
        self.assertEqual(order.user.username, "mame")

    def test_other_browser_cannot_claim_a_guest_order(self):
        from django.test import Client
        order = self.place_order(self.client, self.dress)          # navigateur A (invitée)
        other = Client()                                            # navigateur B
        other.post(reverse("accounts:login"), {"username": "fatou", "password": "pass12345"})
        order.refresh_from_db()
        self.assertIsNone(order.user)

    def test_guest_cart_is_kept_after_login(self):
        self.add_to_cart(self.client, self.dress)
        self.client.post(reverse("accounts:login"), {"username": "awa", "password": "pass12345"})
        cart = Cart.objects.get(user=self.awa, is_ordered=False)
        self.assertEqual(cart.items.get().product, self.dress)

    def test_login_shows_error_on_wrong_password_or_username(self):
        for creds in ({"username": "awa", "password": "mauvais"}, {"username": "inconnue", "password": "pass12345"}):
            resp = self.client.post(reverse("accounts:login"), creds)
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "Nom d&#x27;utilisateur ou mot de passe incorrect")
        resp = self.client.post(reverse("accounts:login"), {"username": "awa", "password": "pass12345"})
        self.assertEqual(resp.status_code, 302)

    def test_mon_compte_and_infos_pages(self):
        self.client.login(username="awa", password="pass12345")
        resp = self.client.get(reverse("accounts:profile"))
        self.assertContains(resp, "Bonjour Awa")
        self.assertContains(resp, reverse("orders:my_orders"))
        resp = self.client.post(reverse("accounts:info"), {
            "first_name": "Awa", "last_name": "Diop", "email": "awa2@example.com", "phone": "771111111"})
        self.assertRedirects(resp, reverse("accounts:info"))
        self.awa.refresh_from_db()
        self.assertEqual(self.awa.email, "awa2@example.com")
        self.assertEqual(Profile.objects.get(user=self.awa).phone, "771111111")


class OrderModelTests(TestCase):
    def test_tracking_steps(self):
        o = Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès")
        states = lambda: [s["state"] for s in o.tracking_steps]
        self.assertEqual(states(), ["done", "todo", "todo", "todo", "todo"])
        o.status = "preparing"
        self.assertEqual(states(), ["done", "done", "current", "todo", "todo"])
        o.status = "delivered"
        self.assertEqual(states(), ["done"] * 5)
        o.status = "cancelled"
        self.assertEqual(o.tracking_steps, [])

    def test_numbers_are_unique_and_sequential(self):
        a = Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès")
        b = Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès")
        self.assertNotEqual(a.number, b.number)
        self.assertEqual(a.number, f"AJL-{a.pk:05d}")


class AdminTests(OrderFlowMixin, TestCase):  # 9, 10, 15, 25
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser("root", "r@example.com", "pass12345")
        self.client.login(username="root", password="pass12345")

    def test_admin_pages_load(self):
        order = Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès")
        OrderItem.objects.create(order=order, product=self.dress, product_name="Aita Dress", unit_price=15000)
        for url in [reverse("admin:orders_order_changelist"),
                    reverse("admin:orders_order_change", args=[order.pk]),
                    reverse("admin:products_product_changelist"),
                    reverse("admin:products_product_change", args=[self.dress.pk]),
                    reverse("dashboard:home")]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_admin_search_accepts_hash(self):
        order = Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès")
        resp = self.client.get(reverse("admin:orders_order_changelist"), {"q": "#" + order.number})
        self.assertContains(resp, order.display_number)


class SizeSystemTests(OrderFlowMixin, TestCase):
    def test_product_page_has_sizes_lengths_and_guide_without_images(self):
        resp = self.client.get(self.dress.get_absolute_url())
        for size in ("XS", "S", "M", "L", "XL", "XXL"):
            self.assertContains(resp, f'name="size" value="{size}"')
        for length in ("1m55", "1m60", "1m65", "1m70", "1m75", "1m80", "1m85", "1m90"):
            self.assertContains(resp, f'<option value="{length}"')
        self.assertContains(resp, "Guide des tailles")
        self.assertContains(resp, "Toutes les dimensions sont indiquées en centimètres (cm).")
        for cell in ("70–78 cm", "60–66 cm", "85–90 cm", "130–135 cm", "100–115 cm", "98–100 cm"):
            self.assertContains(resp, cell)
        for text in ("la partie la plus large de la poitrine", "la partie la plus étroite de la taille",
                     "la partie la plus large des hanches", "de la tête aux pieds"):
            self.assertContains(resp, text)
        guide = resp.content.decode().split('id="sizeGuide"')[1].split("</table>")[0]
        self.assertNotIn("<img", guide)
        self.assertNotContains(resp, "Tour de poitrine (cm)")          # plus de saisie de mensurations
        self.assertNotContains(resp, 'name="bust"')

    def test_size_and_length_saved_in_cart_and_order(self):
        self.client.post(reverse("cart:add_to_cart", args=[self.dress.slug]), {"size": "L", "length": "1m70"})
        item = CartItem.objects.get()
        self.assertEqual((item.size, item.length), ("L", "1m70"))
        self.assertContains(self.client.get(reverse("cart:view_cart")), "Taille : L")
        self.client.post(reverse("orders:checkout"), CHECKOUT)
        self.assertContains(self.client.get(reverse("orders:recap")), "Longueur : 1m70")
        self.client.post(reverse("orders:recap"))
        order_item = Order.objects.latest("id").items.get()
        self.assertEqual((order_item.size, order_item.length), ("L", "1m70"))
        self.assertIn("Taille : L", Order.objects.latest("id").whatsapp_message)

    def test_invalid_or_missing_size_is_rejected(self):
        url = reverse("cart:add_to_cart", args=[self.dress.slug])
        for bad in ({}, {"size": "M"}, {"length": "1m65"}, {"size": "XXXL", "length": "1m65"},
                    {"size": "M", "length": "2m10"}):
            resp = self.client.post(url, bad)
            self.assertRedirects(resp, self.dress.get_absolute_url())
        self.assertFalse(CartItem.objects.exists())

    def test_different_sizes_make_separate_lines_same_size_adds_quantity(self):
        url = reverse("cart:add_to_cart", args=[self.dress.slug])
        self.client.post(url, {"size": "S", "length": "1m65"})
        self.client.post(url, {"size": "M", "length": "1m65"})
        self.client.post(url, {"size": "M", "length": "1m65"})
        self.assertEqual(CartItem.objects.count(), 2)
        self.assertEqual(CartItem.objects.get(size="M").quantity, 2)

    def test_edit_size_in_cart(self):
        self.add_to_cart(self.client, self.dress)
        item = CartItem.objects.get()
        resp = self.client.post(reverse("cart:edit_size", args=[item.pk]), {"size": "XL", "length": "1m80"})
        self.assertRedirects(resp, reverse("cart:view_cart"))
        item.refresh_from_db()
        self.assertEqual((item.size, item.length), ("XL", "1m80"))
        self.assertContains(self.client.get(reverse("cart:edit_size", args=[item.pk])), "Guide des tailles")

    def test_promo_and_totals_unchanged_with_sizes(self):
        self.dress.promo_active, self.dress.promo_price = True, 12500
        self.dress.save()
        order = self.place_order(self.client, self.dress)
        self.assertEqual(order.items.get().unit_price, 12500)
        self.assertIn("Aita Dress ×1 — 12 500 FCFA", order.whatsapp_message)

    def test_old_orders_with_measurements_still_display(self):
        order = Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès")
        OrderItem.objects.create(order=order, product=self.dress, product_name="Aita Dress",
                                 unit_price=15000, bust=92, waist=76, hips=100)
        self.assertIn("Poitrine : 92 cm", order.whatsapp_message)


class HomeSectionsTests(OrderFlowMixin, TestCase):
    def test_collections_replaced_by_bestsellers(self):
        self.dress.is_bestseller = True
        self.dress.save()
        resp = self.client.get(reverse("core:home"))
        self.assertContains(resp, "Nos meilleures ventes")
        self.assertContains(resp, "Les pièces que vous aimez le plus")
        self.assertNotContains(resp, "Nos collections")
        self.assertNotContains(resp, "Des styles pour chaque moment")
        self.assertNotContains(resp, "Ancien modèle")
        self.assertContains(resp, "Nos nouveautés")
        self.assertContains(resp, "Les dernières arrivées")

    def test_no_empty_bestsellers_section(self):
        resp = self.client.get(reverse("core:home"))
        self.assertNotContains(resp, "Nos meilleures ventes")

    def test_bestsellers_not_repeated_in_new_arrivals(self):
        self.dress.is_bestseller, self.dress.is_new = True, True
        self.dress.save()
        self.set.is_new = True
        self.set.save()
        resp = self.client.get(reverse("core:home"))
        self.assertIn(self.dress, list(resp.context["bestsellers"]))
        self.assertNotIn(self.dress, list(resp.context["new_arrivals"]))
        self.assertIn(self.set, list(resp.context["new_arrivals"]))

    def test_out_of_stock_bestseller_is_not_shown(self):
        self.out.is_bestseller = True
        self.out.save()
        self.assertNotIn(self.out, list(self.client.get(reverse("core:home")).context["bestsellers"]))


class NewProductsSeedTests(TestCase):
    NEW = ["Abibatou", "Absatou", "Diarra", "Dior", "Fatima", "Khadidiatou", "Madeleine", "Margot", "Nafissatou"]

    def test_nine_new_products_with_real_photos(self):
        import tempfile
        from django.core.management import call_command
        from django.test import override_settings
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            call_command("seed_ajaley", verbosity=0)
            call_command("seed_ajaley", verbosity=0)               # idempotent
        for name in self.NEW:
            p = Product.objects.get(name=name)
            self.assertTrue(p.is_available, name)
            self.assertTrue(p.is_new, name)
            self.assertFalse(p.is_bestseller, name)
            self.assertGreaterEqual(p.images.count(), 2, name)
            self.assertTrue(p.images.exists(), name)
            self.assertIn(p.category.slug, ("robes", "ensembles"), name)
            self.assertIn(p.price, (15000, 20000, 25000), name)
            self.assertNotIn("Ancien modèle", p.description)
        self.assertEqual(Product.objects.filter(name__in=self.NEW).count(), 9)
        self.assertEqual(Product.objects.count(), 23)


class AuditFixesTests(OrderFlowMixin, TestCase):
    def test_language_switch_only_redirects_inside_the_site(self):
        resp = self.client.get(reverse("set_language"), {"lang": "en", "next": "https://evil.example/"})
        self.assertRedirects(resp, "/", fetch_redirect_response=False)
        resp = self.client.get(reverse("set_language"), {"lang": "en", "next": "/boutique/"})
        self.assertRedirects(resp, "/boutique/", fetch_redirect_response=False)
        self.assertEqual(resp.cookies["django_language"].value, "en")
        resp = self.client.get(reverse("set_language"), {"lang": "xx", "next": "/"})
        self.assertNotIn("django_language", resp.cookies)

    def test_browsing_does_not_create_carts(self):
        self.client.get(reverse("core:home"))
        self.client.get(reverse("products:catalog"))
        self.assertEqual(Cart.objects.count(), 0)
        self.add_to_cart(self.client, self.dress)
        self.assertContains(self.client.get(reverse("core:home")), 'class="cart-badge">1<')

    def test_favorite_toggle_ignores_external_referer(self):
        User.objects.create_user("awa", password="pass12345")
        self.client.login(username="awa", password="pass12345")
        url = reverse("products:toggle_favorite", args=[self.dress.slug])
        resp = self.client.post(url, HTTP_REFERER="https://evil.example/")
        self.assertRedirects(resp, reverse("products:catalog"), fetch_redirect_response=False)
        resp = self.client.post(url, HTTP_REFERER="http://testserver/boutique/")
        self.assertEqual(resp.url, "http://testserver/boutique/")

    def test_order_reference_is_long_and_random(self):
        refs = {Order.objects.create(first_name="A", last_name="B", phone="1", city="Thiès").reference
                for _ in range(5)}
        self.assertEqual(len(refs), 5)
        self.assertTrue(all(r.startswith("AJA-") and len(r) == 14 for r in refs))

    def test_state_changing_views_refuse_get(self):
        self.add_to_cart(self.client, self.dress)
        item = CartItem.objects.get()
        for name, args in (("cart:update_quantity", [item.pk]), ("cart:remove_item", [item.pk])):
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 405)
        self.assertEqual(CartItem.objects.get().quantity, 1)
        User.objects.create_user("awa", password="pass12345")
        self.client.post(reverse("accounts:login"), {"username": "awa", "password": "pass12345"})
        resp = self.client.get(reverse("products:toggle_favorite", args=[self.dress.slug]))
        self.assertEqual(resp.status_code, 405)
        resp = self.client.post(reverse("cart:update_quantity", args=[item.pk]), {"action": "increase"})
        self.assertEqual(resp.status_code, 302)
