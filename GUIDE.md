# Guide d'installation et de test — AJA LEY

Ce guide explique **comment installer, lancer et tester** le site de bout en bout.
La présentation du projet se trouve dans le `README.md`.

Durée estimée : 10 minutes d'installation, 20 minutes pour tout tester.

---

## 1. Prérequis

- **Python 3.10 ou plus récent** (`python3 --version`)
- **pip** (installé avec Python)
- **Git**
- un **environnement virtuel** (`venv`, fourni avec Python)
- un navigateur web

---

## 2. Installation du projet

```bash
# 1. Cloner le projet puis entrer dans le dossier
git clone <adresse-du-depot-github>
cd <nom-du-dossier-du-projet>        # le dossier qui contient manage.py

# 2. Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate             # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer la base de données
python manage.py migrate

# 5. Charger le catalogue (catégories, 23 produits et leurs photos)
python manage.py seed_ajaley

# 6. Créer un compte administrateur (voir la section 13)
python manage.py createsuperuser
```

> L'étape 5 est indispensable : sans elle, la boutique est vide. Elle peut être relancée sans risque
> (elle ne modifie jamais un produit existant).

---

## 3. Lancer le site

```bash
python manage.py runserver
```

Ouvrir ensuite dans le navigateur : **http://127.0.0.1:8000/**

Garder la **même adresse** pendant tous les tests (`127.0.0.1` ou `localhost`, mais pas les deux) :
le navigateur conserve la session et le panier séparément pour chacune des deux adresses.

| Page | Adresse |
|---|---|
| Accueil | http://127.0.0.1:8000/ |
| Boutique | http://127.0.0.1:8000/boutique/ |
| Panier | http://127.0.0.1:8000/panier/ |
| Inscription | http://127.0.0.1:8000/compte/inscription/ |
| Connexion | http://127.0.0.1:8000/compte/connexion/ |
| Mon compte | http://127.0.0.1:8000/compte/profil/ |
| Mes commandes | http://127.0.0.1:8000/commandes/mes-commandes/ |
| Commande internationale | http://127.0.0.1:8000/commandes/checkout/international/ |
| Administration | http://127.0.0.1:8000/admin/ |
| Tableau de bord (compte administrateur) | http://127.0.0.1:8000/dashboard/ |
| API produits | http://127.0.0.1:8000/api/products/ |

---

## 4. Créer un compte client

1. Ouvrir le site, cliquer sur l'icône « personne » en haut à droite (Connexion), puis ouvrir
   **http://127.0.0.1:8000/compte/inscription/**.
2. Remplir le formulaire (prénom, nom — facultatif —, email, nom d'utilisateur, mot de passe) et valider.
3. Le site connecte automatiquement la nouvelle cliente et ouvre **Mon compte**.
4. Vérifier la page « Mon compte » : *Mes commandes*, *Mes informations*, *Mes favoris*,
   *Se déconnecter*.
5. Ouvrir **Mes informations** : modifier le nom, l'email ou le téléphone, puis enregistrer.
6. Ouvrir **Mes commandes** : la liste est vide tant qu'aucune commande n'a été passée.

> Un seul compte peut être connecté par navigateur. Pour tester en même temps le compte client
> et l'administration, utiliser deux navigateurs, ou une fenêtre de navigation privée.

---

## 5. Tester le catalogue

1. Ouvrir **Boutique** (menu du haut) : les produits s'affichent avec leurs photos.
2. Essayer la recherche et les filtres (catégorie, prix).
3. Cliquer sur un produit pour ouvrir sa **fiche** : consulter les photos.
4. Cliquer sur **Guide des tailles** : une fenêtre s'ouvre avec les explications et le tableau
   (XS à XXL). La fermer avec la croix, la touche Échap ou un clic à côté.
5. Choisir une **taille** (XS, S, M, L, XL ou XXL).
6. Choisir une **longueur** dans la liste (1m55 à 1m90) : elle est obligatoire.
7. Cliquer sur **Ajouter au panier**.

Si la taille ou la longueur manque, le site refuse l'ajout et affiche un message.

---

## 6. Tester le panier

1. Le panier s'ouvre après l'ajout (ou via l'icône panier en haut à droite).
2. Vérifier le produit, son prix, la **taille** et la **longueur** affichées.
3. Cliquer sur **Modifier la taille** pour changer la taille ou la longueur, puis valider.
4. Utiliser **+** et **−** pour la quantité, ou **Supprimer** pour retirer l'article.
5. Ajouter la même pièce dans une autre taille : elle forme une **deuxième ligne** du panier.
6. Cliquer sur **Passer la commande**.

---

## 7. Tester une commande nationale

Le checkout demande : prénom, nom, téléphone, email (facultatif), **région**, zone de livraison
(pour Dakar et Thiès), quartier et instructions. Aucune adresse complète n'est demandée.
Les frais et le total du bloc « Votre commande » se mettent à jour dès que la région ou la zone change.

**Scénario A — Dakar-ville**

- Région : **Dakar**
- Zone de livraison : **Dakar-ville — 2 000 FCFA**
- Résultat attendu : livraison **2 000 FCFA**

**Scénario B — Autre localité de Thiès**

- Région : **Thiès**
- Zone de livraison : **Autre localité — 2 000 FCFA**
- Ville / localité : **Mbour**
- Résultat attendu : livraison **2 000 FCFA** (Thiès-ville donnerait 1 000 FCFA)

**Terminer la commande :**

1. Cliquer sur **Voir le récapitulatif** et vérifier les informations, les articles et le total.
2. Cliquer sur **Confirmer ma commande**.
3. La page « Commande enregistrée » affiche le **numéro de commande** (`#AJL-00001`, etc.).
4. Cliquer sur **Commander via WhatsApp** : WhatsApp s'ouvre vers le numéro du Sénégal avec le message
   déjà rédigé (numéro de commande, informations de la cliente, articles avec taille et longueur,
   livraison, total). **Rien n'est envoyé automatiquement.**

Les autres régions du Sénégal (Louga, Saint-Louis, etc.) n'ont pas de zone : la livraison est de 2 000 FCFA.

---

## 8. Tester la livraison en banlieue

- Région : **Dakar**
- Zone de livraison : **Banlieue dakaroise — 4 000 FCFA**
- Ville / localité : **Guédiawaye** (autres choix : Keur Massar, Rufisque, Diamniadio, Mbao, ZAC Mbao,
  Bargny, Sangalkam, Autre)
- Quartier : par exemple **Ndiarème**

Résultat attendu : livraison **4 000 FCFA**. Le quartier sert seulement à préciser l'adresse : il ne
change pas le tarif. Avec « Autre », un champ apparaît pour préciser la localité.

---

## 9. Tester une commande internationale

1. Dans le checkout, cliquer sous le formulaire sur **Commander depuis l'international →**
   (ou ouvrir directement http://127.0.0.1:8000/commandes/checkout/international/).
2. Remplir le formulaire : le téléphone doit commencer par l'indicatif (`+33 6 12 34 56 78`).
   Choisir le pays **France**, indiquer une ville (Paris) et, si on le souhaite, une zone.
3. Vérifier que la livraison affiche **À confirmer** et que le total est nommé **Total produits**.
4. Cliquer sur **Voir le récapitulatif**, puis **Confirmer ma commande**.
5. La page affiche **Commande enregistrée !** et le message demandant de contacter AJA LEY sur WhatsApp.
6. Cliquer sur **Confirmer sur WhatsApp →** : WhatsApp s'ouvre vers le numéro international
   **+1 317 319 9999** avec un message prérempli (numéro de commande, nom, pays, montant des produits,
   articles avec taille et longueur). Le message n'est pas envoyé automatiquement.

Il n'y a ni paiement en ligne ni API WhatsApp : les frais sont confirmés par AJA LEY sur WhatsApp.

---

## 10. Tester les promotions

Aucun produit n'est en promotion au départ : la rubrique **Promotions** n'apparaît donc pas dans le menu.

1. Se connecter à **/admin/** avec le compte administrateur, puis ouvrir **Produits**.
2. Ouvrir un produit disponible. Dans « Prix et promotion » : cocher **Promotion activée** et indiquer
   un **Prix promotionnel** inférieur au prix normal (ex. 15 000 → 12 500 FCFA). Enregistrer.
   (Ces champs sont aussi modifiables directement dans la liste des produits.)
3. Revenir sur le site et vérifier :
   - la carte du produit : badge de réduction (**-17 %**), prix normal barré, prix promotionnel ;
   - la fiche produit : même affichage ;
   - la rubrique **Promotions** dans le menu et la section **Offres du moment** sur l'accueil ;
   - le **panier** : le prix promotionnel est utilisé ;
   - le récapitulatif, la **commande** et le message WhatsApp : même prix promotionnel.
4. Décocher la promotion dans l'admin : le prix normal revient et la rubrique **Promotions** disparaît.

Un produit en rupture de stock (décocher « Disponible » dans l'admin) reste visible mais ne peut pas être
commandé, même avec un ancien prix promotionnel.

---

## 11. Tester un compte client (suivi de commande)

1. Se connecter avec le compte client créé à la section 4, puis passer une commande (sections 5 à 7).
2. La commande est rattachée automatiquement au compte.
3. Ouvrir **Mon compte → Mes commandes** : la commande apparaît avec son numéro, ses articles, son total,
   son **statut** (« En attente » au départ) et la date de livraison (« à confirmer » au départ).
4. Cliquer sur la commande : le **détail** affiche le suivi visuel, les articles avec taille et longueur,
   la livraison et le total.
5. Dans l'administration (section 13), passer la commande en **Confirmée** puis **En préparation** et
   renseigner une **date de livraison prévue** : recharger la page de la commande côté cliente pour voir
   le changement.
6. Passer la commande en **Livrée** ou **Annulée** : elle disparaît de « Mes commandes ».

Une cliente ne voit que ses propres commandes : l'adresse d'une commande d'une autre cliente renvoie
une erreur 404.

---

## 12. Tester le mode invité

1. Se déconnecter (ou ouvrir une fenêtre de navigation privée).
2. Ajouter un produit au panier (taille et longueur), puis passer la commande **sans créer de compte**.
3. La commande est enregistrée et la page de confirmation s'affiche normalement, avec le bouton WhatsApp.
4. Si la cliente se connecte ou crée un compte ensuite **dans le même navigateur**, sa commande invitée
   est rattachée à son compte et apparaît dans « Mes commandes ».

---

## 13. Tester l'administration

Un compte administrateur est nécessaire. Il se crée avec la commande :

```bash
python manage.py createsuperuser
```

Le projet ne fournit **aucun identifiant prédéfini** : choisir soi-même le nom d'utilisateur et le mot de passe.

1. Ouvrir **http://127.0.0.1:8000/admin/** et se connecter.
2. **Commandes** : la liste montre le numéro, la cliente, les produits, le total, le statut, la date de
   commande et la date de livraison prévue. Le **statut** et la **date de livraison** se modifient
   directement dans la liste (bouton « Enregistrer » en bas). La recherche accepte `#AJL-00001`.
3. **Produits** : prix, promotion, disponibilité, « Nouveau », « Meilleure vente », photos.
4. **Frais de livraison** : tarif facultatif par région sans zones (les tarifs par défaut sont dans
   `ajaley/settings.py`).
5. Ouvrir aussi **http://127.0.0.1:8000/dashboard/** (même compte) : statistiques et dernières commandes.

---

## 14. Vérification finale

```
[ ] Le site démarre
[ ] Le catalogue fonctionne
[ ] Les images s'affichent
[ ] Une fiche produit fonctionne
[ ] Le guide des tailles fonctionne
[ ] La taille fonctionne
[ ] La longueur fonctionne
[ ] Le panier fonctionne
[ ] Une commande nationale fonctionne
[ ] Dakar-ville affiche 2 000 FCFA
[ ] Banlieue dakaroise affiche 4 000 FCFA
[ ] Mbour affiche 2 000 FCFA
[ ] Une commande internationale fonctionne
[ ] WhatsApp fonctionne
[ ] Les promotions fonctionnent
[ ] Le compte client fonctionne
[ ] La commande invitée fonctionne
[ ] L'administration fonctionne
```

### Vérifications techniques (facultatif)

```bash
python manage.py check                    # vérifie la configuration Django
python manage.py makemigrations --check   # doit répondre « No changes detected »
python manage.py test                     # lance les tests automatiques
```

### En cas de problème

- **Page « Interdit (403) — vérification CSRF »** : recharger la page du formulaire (Ctrl+F5) et garder la
  même adresse (`127.0.0.1` ou `localhost`) pendant toute la session.
- **Erreur « Invalid HTTP_HOST header »** : le serveur n'accepte par défaut que `localhost` et `127.0.0.1`.
  Pour une autre adresse : `export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,<autre-adresse>`
  avant `runserver` (voir `.env.example`).
- **Boutique vide** : lancer `python manage.py seed_ajaley`.
- **Polices différentes de la maquette** : elles se chargent depuis Google Fonts et demandent une connexion internet.
- **Le bouton WhatsApp ouvre une page web** : normal si l'application WhatsApp n'est pas installée sur
  l'ordinateur ; le message prérempli apparaît dans WhatsApp Web.
