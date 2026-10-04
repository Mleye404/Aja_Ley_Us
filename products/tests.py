from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


def make_product(name="Aita Dress", price=15000, **kw):
    cat, _ = Category.objects.get_or_create(slug="robes", defaults={"name": "Robes"})
    return Product.objects.create(name=name, price=price, category=cat, **kw)


class PromotionModelTests(TestCase):
    def test_discount_percent_is_computed(self):  # 16
        p = make_product(promo_active=True, promo_price=12500)
        self.assertTrue(p.is_on_promo)
        self.assertEqual(p.discount_percent, 17)
        self.assertEqual(p.current_price, 12500)

    def test_normal_price_kept_when_promo_disabled(self):
        p = make_product(promo_active=True, promo_price=12500)
        p.promo_active = False
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.price, 15000)
        self.assertEqual(p.promo_price, 12500)
        self.assertEqual(p.current_price, 15000)
        self.assertEqual(p.discount_percent, 0)

    def test_out_of_stock_product_is_not_on_promo(self):  # 23
        p = make_product(is_available=False, promo_active=True, promo_price=12500)
        self.assertFalse(p.is_on_promo)
        self.assertEqual(p.current_price, 15000)
        self.assertFalse(Product.objects.on_promo().exists())

    def test_clean_rejects_invalid_promo(self):
        with self.assertRaises(ValidationError):
            make_product(promo_active=True, promo_price=None).full_clean()
        with self.assertRaises(ValidationError):
            make_product(name="B", promo_active=True, promo_price=16000).full_clean()


class PromotionDisplayTests(TestCase):
    def test_promotions_nav_appears_only_with_active_promo(self):  # 21, 22
        p = make_product()
        resp = self.client.get(reverse("core:home"))
        self.assertNotContains(resp, "?promo=1")
        self.assertNotContains(resp, "Offres du moment")

        p.promo_active, p.promo_price = True, 12500
        p.save()
        resp = self.client.get(reverse("core:home"))
        self.assertContains(resp, "?promo=1")
        self.assertContains(resp, "Offres du moment")

        p.promo_active = False
        p.save()
        resp = self.client.get(reverse("core:home"))
        self.assertNotContains(resp, "?promo=1")

    def test_promo_page_redirects_when_no_promotion(self):
        make_product()
        resp = self.client.get(reverse("products:catalog") + "?promo=1")
        self.assertRedirects(resp, reverse("products:catalog"))

    def test_card_shows_badge_and_struck_price(self):  # 15, 17
        make_product(promo_active=True, promo_price=12500)
        resp = self.client.get(reverse("products:catalog"))
        self.assertContains(resp, "-17")
        self.assertContains(resp, "price-old")
        self.assertContains(resp, "15\u00a0000")
        self.assertContains(resp, "12\u00a0500")

    def test_out_of_stock_product_stays_visible_without_promo(self):  # 23
        make_product(is_available=False, promo_active=True, promo_price=12500)
        resp = self.client.get(reverse("products:catalog"))
        self.assertContains(resp, "Rupture de stock")
        self.assertNotContains(resp, "price-old")
