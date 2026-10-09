import unicodedata

# Les 14 régions administratives du Sénégal (liste déroulante du checkout national).
SENEGAL_REGIONS = [
    "Dakar", "Diourbel", "Fatick", "Kaffrine", "Kaolack", "Kédougou", "Kolda",
    "Louga", "Matam", "Saint-Louis", "Sédhiou", "Tambacounda", "Thiès", "Ziguinchor",
]

SENEGAL_NAME = "Sénégal"

# « Zones de livraison AJA LEY » : on ne reproduit PAS le découpage administratif du Sénégal.
# Seules Dakar et Thiès ont des zones ; les autres régions ont un tarif unique.
OTHER_LOCALITY = "Autre"

DELIVERY_ZONES = {
    "Dakar": [
        {"name": "Dakar-ville", "fee_setting": "SHIPPING_DAKAR", "locality": False, "localities": []},
        {"name": "Banlieue dakaroise", "fee_setting": "SHIPPING_DAKAR_BANLIEUE", "locality": True,
         "localities": ["Guédiawaye", "Keur Massar", "Rufisque", "Diamniadio", "Mbao", "ZAC Mbao",
                        "Bargny", "Sangalkam", OTHER_LOCALITY]},
    ],
    "Thiès": [
        {"name": "Thiès-ville", "fee_setting": "SHIPPING_THIES", "locality": False, "localities": []},
        {"name": "Autre localité", "fee_setting": "SHIPPING_THIES_OTHER", "locality": True,
         "localities": ["Mbour", "Tivaouane", "Joal-Fadiouth", OTHER_LOCALITY]},
    ],
}

# Aide affichée sous la zone de livraison quand la région est Dakar.
DAKAR_BANLIEUE_HELP = ("Banlieue dakaroise : Keur Massar, ZAC Mbao, Guédiawaye, Rufisque, Diamniadio, "
                       "Bargny, Sangalkam, Mbao et autres localités de la banlieue.")


def zones_for(region):
    return DELIVERY_ZONES.get(region, [])

# Pays proposés dans le formulaire international (le Sénégal a son propre parcours).
_COUNTRIES = [
    "Afghanistan", "Afrique du Sud", "Albanie", "Algérie", "Allemagne", "Andorre", "Angola",
    "Arabie saoudite", "Argentine", "Arménie", "Australie", "Autriche", "Azerbaïdjan",
    "Bahamas", "Bahreïn", "Bangladesh", "Barbade", "Belgique", "Belize", "Bénin", "Bhoutan",
    "Biélorussie", "Birmanie", "Bolivie", "Bosnie-Herzégovine", "Botswana", "Brésil", "Brunei",
    "Bulgarie", "Burkina Faso", "Burundi", "Cambodge", "Cameroun", "Canada", "Cap-Vert", "Chili",
    "Chine", "Chypre", "Colombie", "Comores", "Congo (Brazzaville)", "Congo (Kinshasa)",
    "Corée du Sud", "Costa Rica", "Côte d'Ivoire", "Croatie", "Cuba", "Danemark", "Djibouti",
    "Dominique", "Égypte", "Émirats arabes unis", "Équateur", "Érythrée", "Espagne", "Estonie",
    "Eswatini", "États-Unis", "Éthiopie", "Fidji", "Finlande", "France", "Gabon", "Gambie",
    "Géorgie", "Ghana", "Grèce", "Guadeloupe", "Guatemala", "Guinée", "Guinée-Bissau",
    "Guinée équatoriale", "Guyana", "Guyane française", "Haïti", "Honduras", "Hongrie",
    "Île Maurice", "Inde", "Indonésie", "Irak", "Iran", "Irlande", "Islande", "Israël", "Italie",
    "Jamaïque", "Japon", "Jordanie", "Kazakhstan", "Kenya", "Koweït", "Laos", "Lesotho",
    "Lettonie", "Liban", "Liberia", "Libye", "Liechtenstein", "Lituanie", "Luxembourg",
    "Macédoine du Nord", "Madagascar", "Malaisie", "Malawi", "Maldives", "Mali", "Malte", "Maroc",
    "Martinique", "Mauritanie", "Mayotte", "Mexique", "Moldavie", "Monaco", "Mongolie",
    "Monténégro", "Mozambique", "Namibie", "Népal", "Nicaragua", "Niger", "Nigeria", "Norvège",
    "Nouvelle-Zélande", "Oman", "Ouganda", "Ouzbékistan", "Pakistan", "Panama", "Paraguay",
    "Pays-Bas", "Pérou", "Philippines", "Pologne", "Portugal", "Qatar", "République centrafricaine",
    "République dominicaine", "République tchèque", "La Réunion", "Roumanie", "Royaume-Uni",
    "Russie", "Rwanda", "Saint-Marin", "Sao Tomé-et-Principe", "Serbie", "Seychelles",
    "Sierra Leone", "Singapour", "Slovaquie", "Slovénie", "Somalie", "Soudan", "Soudan du Sud",
    "Sri Lanka", "Suède", "Suisse", "Suriname", "Syrie", "Tadjikistan", "Taïwan", "Tanzanie",
    "Tchad", "Thaïlande", "Togo", "Trinité-et-Tobago", "Tunisie", "Turquie", "Ukraine", "Uruguay",
    "Venezuela", "Vietnam", "Yémen", "Zambie", "Zimbabwe",
]


def strip_accents(value):
    return "".join(c for c in unicodedata.normalize("NFD", (value or "").strip().lower())
                   if unicodedata.category(c) != "Mn")


COUNTRIES = sorted(_COUNTRIES, key=strip_accents)


def is_senegal(country):
    return strip_accents(country) == "senegal"
