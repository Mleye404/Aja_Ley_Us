import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Category, Product, ProductImage

# Photos livrées avec le projet (versionnées dans Git) : le seed fonctionne après un simple `git clone`.
ASSETS_DIR = os.path.join(settings.BASE_DIR, "products", "fixtures", "source_photos")

CATEGORIES = [
    {"name": "Robes", "slug": "robes", "image": "Aita_dress1.jpeg"},
    {"name": "Ensembles", "slug": "ensembles", "image": "Rockaya_set1.jpeg"},
    {"name": "Abayas", "slug": "abayas", "image": "Imani_Bubu1.jpeg"},
    {"name": "Cérémonie", "slug": "ceremonie", "image": "Katy_dress1.jpeg"},
]

# (nom, prix, disponible, catégorie_slug, photos dans source_photos)
PRODUCTS = [
    ("Aita Dress", 15000, True, "robes", ["Aita_dress1.jpeg", "Aita_dress2.jpeg"]),
    ("Shabi Dress", 15000, True, "robes", ["Shabi dress 1.jpeg", "Shabi dress 2.jpeg"]),
    ("Pamela Set", 14000, True, "ensembles", ["Pamela_set1.jpeg", "Pamela_set2.jpeg"]),
    ("Farida Set", 14000, True, "ensembles", ["Farida_set1.jpeg", "Farida_set2.jpeg"]),
    ("Rokhaya Set", 15000, True, "ensembles", ["Rockaya_set1.jpeg", "Rockaya_set2.jpeg"]),
    ("Mously Set", 15000, True, "ensembles", ["Mously set1 .jpeg", "Mously set2.jpeg", "Mously set3.jpeg"]),
    ("Baaly Dress", 14000, True, "robes", ["Baaly_dress1.jpeg", "Baaly_dress2.jpeg", "Baaly_dress3.jpeg"]),
    ("Fatwa", 14000, True, "ensembles", ["Fatwa1.jpeg", "Fatwa2.jpeg", "Fatwa3.jpeg"]),
    ("Sabelle", 12000, True, "robes", ["Sabelle1.jpeg"]),
    ("Amara Dress", 33000, False, "ceremonie", ["Amara_dress1.jpeg", "Amara_dress2.jpeg", "Amara_dress3.jpeg"]),
    ("Makena Bubu", 45000, False, "abayas", ["Makena_bubu1.jpeg", "Makena_bubu2.jpeg"]),
    ("Nefertiti", 20000, False, "ceremonie", ["Nefertiti_setPants1.jpeg", "Nefertiti_setPants2.jpeg"]),
    ("Katy Dress", 30000, False, "ceremonie", ["Katy_dress1.jpeg", "Katy_dress2.jpeg"]),
    ("Imani Bubu", 20000, False, "abayas", ["Imani_Bubu1.jpeg", "Imani_bubu2.jpeg", "Imani_bubu3.jpeg"]),
    # --- 9 nouveaux produits (vraies photos), disponibles, prix PROVISOIRES à ajuster dans l'admin ---
    ("Abibatou", 15000, True, "ensembles", ["Abibatou1.jpeg", "Abibatou2.jpeg", "Abibatou3.jpeg"]),
    ("Absatou", 20000, True, "robes", ["Absatou1.jpeg", "Absatou2.jpeg"]),
    ("Diarra", 25000, True, "robes", ["Diarra1.jpeg", "Diarra2.jpeg"]),
    ("Dior", 25000, True, "robes", ["Dior1.jpeg", "Dior2.jpeg", "Dior3.jpeg"]),
    ("Fatima", 20000, True, "ensembles", ["Fatima1.jpeg", "Fatima2.jpeg"]),
    ("Khadidiatou", 25000, True, "robes", ["Khadidiatou1.jpeg", "Khadidiatou2.jpeg"]),
    ("Madeleine", 20000, True, "robes", ["Madeleine1.jpeg", "Madeleine2.jpeg", "Madeleine3.jpeg"]),
    ("Margot", 15000, True, "robes", ["Margot1.jpeg", "Margot2.jpeg", "Margot3.jpeg"]),
    ("Nafissatou", 15000, True, "robes", ["Nafissatou1.jpeg", "Nafissatou2.jpeg", "Nafissatou3.jpeg"]),
]

# « Nos meilleures ventes » (page d'accueil) : sélection manuelle parmi les anciens modèles
# disponibles. Modifiable ensuite dans l'admin (case « Meilleure vente » du produit).
BESTSELLERS = {"Aita Dress", "Pamela Set", "Rokhaya Set", "Baaly Dress"}


class Command(BaseCommand):
    help = "Charge les catégories, les produits réels AJA LEY (23 modèles) et leurs vraies photos (livrées avec le projet)."

    def handle(self, *args, **options):
        if not os.path.isdir(ASSETS_DIR):
            self.stdout.write(self.style.ERROR(
                f"Dossier de photos source introuvable : {ASSETS_DIR}\n"
                "Vérifie que le dossier products/fixtures/source_photos/ est bien présent "
                "dans ton clone du projet (il doit être versionné dans Git)."
            ))
            return

        media_products_dir = os.path.join(settings.MEDIA_ROOT, "products")
        media_categories_dir = os.path.join(settings.MEDIA_ROOT, "categories")
        os.makedirs(media_products_dir, exist_ok=True)
        os.makedirs(media_categories_dir, exist_ok=True)

        # ---- Catégories ----
        cats = {}
        for c in CATEGORIES:
            cat, _ = Category.objects.get_or_create(slug=c["slug"], defaults={"name": c["name"]})
            cats[c["slug"]] = cat
            if not cat.image:
                src = os.path.join(ASSETS_DIR, c["image"])
                if os.path.exists(src):
                    dst_rel = os.path.join("categories", f"{c['slug']}.jpeg")
                    shutil.copyfile(src, os.path.join(settings.MEDIA_ROOT, dst_rel))
                    cat.image = dst_rel
                    cat.save()
                else:
                    self.stdout.write(self.style.WARNING(f"Photo de catégorie introuvable : {c['image']}"))
        self.stdout.write(self.style.SUCCESS(f"{len(cats)} catégories prêtes."))

        # ---- Produits + photos ----
        # Idempotent : un produit existant n'est jamais modifié ; s'il n'a aucune photo, on les ajoute.
        created_count = 0
        completed_count = 0
        for name, price, available, cat_slug, images in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "price": price,
                    "is_available": available,
                    "category": cats[cat_slug],
                    "is_featured": available,
                    "is_new": available,
                    "is_bestseller": available and name in BESTSELLERS,
                    "description": f"{name} — pièce AJA LEY disponible du XS au XXL. "
                                    f"For every mood. Every you.",
                },
            )
            if created:
                created_count += 1
            elif product.images.exists():
                continue  # déjà créé ET déjà illustré : rien à faire
            else:
                completed_count += 1

            added = 0
            for i, filename in enumerate(images):
                src = os.path.join(ASSETS_DIR, filename)
                if not os.path.exists(src):
                    self.stdout.write(self.style.WARNING(f"Fichier introuvable : {filename}"))
                    continue
                safe_name = f"{product.slug}-{i+1}.jpeg"
                dst_rel = os.path.join("products", safe_name)
                dst_abs = os.path.join(settings.MEDIA_ROOT, dst_rel)
                shutil.copyfile(src, dst_abs)
                ProductImage.objects.get_or_create(product=product, order=i, defaults={"image": dst_rel})
                added += 1
            status = "disponible" if available else "RUPTURE DE STOCK"
            self.stdout.write(self.style.SUCCESS(f"✓ {name} ({price} FCFA, {status}, {added} photo(s))"))

        self.stdout.write(self.style.SUCCESS(
            f"\nTerminé : {created_count} produit(s) créé(s), {completed_count} complété(s) en photos, "
            f"sur {len(PRODUCTS)} au total."
        ))
