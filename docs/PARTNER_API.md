# Jumbo Pneus — Documentation API partenaire

Version : v1
Contact : cheng@jumbopneus.fr

Cette API permet à un service externe (par ex. assistant téléphonique AI) de
rechercher des pneus dans notre stock et d'obtenir, pour chaque référence :
marque, modèle, dimension, indices, prix TTC, prix promo éventuel et
disponibilité immédiate.

---

## 1. URL de base

```
https://api.jumbopneus.shop
```

---

## 2. Authentification

Toutes les requêtes doivent inclure un jeton Bearer :

```
Authorization: Bearer <PARTNER_API_TOKEN>
```

Le token vous est communiqué hors-bande (e-mail chiffré ou échange direct).
**Il est dédié à votre intégration** et peut être révoqué sans impacter nos
autres systèmes internes.

Codes HTTP d'authentification :

| Code | Signification                                        |
| ---- | ---------------------------------------------------- |
| 401  | Token manquant ou invalide                           |
| 503  | Token non configuré côté serveur (incident interne)  |

---

## 3. Endpoint : recherche de pneus

```
GET /api/v1/tire-search
```

### 3.1 Paramètres de requête

Au moins un critère doit être fourni (`ean`, ou dimension, ou `brand`, ou `q`).

| Paramètre       | Type    | Exemple             | Description                                                  |
| --------------- | ------- | ------------------- | ------------------------------------------------------------ |
| `width`         | int     | `205`               | Largeur en mm                                                |
| `aspect`        | int     | `55`                | Série (hauteur)                                              |
| `diameter`      | int     | `16`                | Diamètre de jante en pouces                                  |
| `brand`         | string  | `MICH`, `Michelin`  | Code marque ou nom (insensible à la casse)                   |
| `q`             | string  | `primacy 4`         | Recherche libre sur libellé ou modèle                        |
| `season`        | string  | `summer`            | `summer` \| `winter` \| `4s` (alias FR acceptés : `ete`, `hiver`, `4saisons`) |
| `runflat`       | bool    | `true`              | Filtrer uniquement les pneus Run-Flat                        |
| `tier`          | string  | `premium`           | `premium` \| `moyenne_gamme` \| `premier_prix` (alias FR acceptés : `premier prix`, `moyenne gamme`, `haut de gamme`, `budget`...) |
| `ean`           | string  | `3528705349843`     | Lookup direct par code-barres EAN-13                         |
| `in_stock_only` | bool    | `true` *(défaut)*   | Si `true`, ne retourne que les références en stock immédiat  |
| `limit`         | int     | `50` *(défaut)*     | Nombre max de résultats (1–100)                              |

### 3.2 Codes de saison renvoyés

| Valeur     | Signification     |
| ---------- | ----------------- |
| `summer`   | Pneu été          |
| `winter`   | Pneu hiver        |
| `4s`       | Toutes saisons    |
| `null`     | Non classifié     |

### 3.2bis Codes de gamme (tier) renvoyés

| Valeur (`tier`)  | Label (`tier_label`) | Signification                                                              |
| ---------------- | -------------------- | -------------------------------------------------------------------------- |
| `premium`        | `Premium`            | Haut de gamme : Michelin, Continental, Bridgestone, Pirelli, Goodyear, Dunlop, Hankook |
| `moyenne_gamme`  | `Moyenne Gamme`      | Milieu de gamme : Kumho, Nexen, Kleber, Uniroyal, Falken, Yokohama, Nokian, Toyo, Nankang, Vredestein, BFGoodrich, GT-Radial, Firestone |
| `premier_prix`   | `Premier Prix`       | Tout le reste (entrée de gamme / budget). Par défaut, toute marque non classée Premium ou Moyenne Gamme est considérée Premier Prix. |

La classification est gérée côté Jumbo Pneus. `tier` est toujours renseigné,
il ne renvoie jamais `null`.

### 3.3 Exemples cURL

**Recherche par dimension :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/tire-search?width=205&aspect=55&diameter=16"
```

**Dimension + marque + saison été uniquement :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/tire-search?width=225&aspect=45&diameter=17&brand=MICH&season=summer"
```

**Recherche libre sur un modèle :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/tire-search?q=primacy%204&limit=10"
```

**Lookup direct par EAN :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/tire-search?ean=3528705349843"
```

**Recherche par gamme (le client demande "du premier prix") :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/tire-search?width=205&aspect=55&diameter=16&tier=premier_prix"
```

**Combinaison gamme + saison :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/tire-search?width=225&aspect=45&diameter=17&tier=premium&season=summer"
```

### 3.4 Format de la réponse

```json
{
  "count": 2,
  "items": [
    {
      "sku": "MIPRI4205551691W",
      "ean": "3528705349843",
      "brand": "MICHELIN",
      "brand_code": "MICH",
      "model": "PRIMACY 4",
      "designation": "205/55R16 91W PRIMACY 4",
      "dimension": "205/55R16",
      "width": 205,
      "aspect_ratio": 55,
      "diameter": 16,
      "load_index": "91",
      "speed_index": "W",
      "season": "summer",
      "runflat": false,
      "tier": "premium",
      "tier_label": "Premium",
      "labels": {
        "fuel_efficiency": "A",
        "wet_grip": "B",
        "noise_db": 70
      },
      "price_ttc": 152.40,
      "promo": {
        "price_ttc": 139.90,
        "label": "Promo Été 2026",
        "id": "PROMO_ETE_2026"
      },
      "in_stock": true,
      "stock_qty": 8
    }
  ],
  "filters": {
    "width": 205, "aspect": 55, "diameter": 16,
    "brand": null, "q": null, "season": null,
    "runflat": null, "ean": null, "in_stock_only": true
  }
}
```

### 3.5 Sémantique des champs

| Champ              | Description                                                      |
| ------------------ | ---------------------------------------------------------------- |
| `sku`              | Référence interne Jumbo Pneus                                    |
| `ean`              | EAN-13 du fabricant (peut être `null` si non renseigné)          |
| `brand`            | Nom commercial de la marque                                      |
| `brand_code`       | Code interne marque (utile pour filtrer en retour)               |
| `model`            | Nom du modèle (profil)                                           |
| `designation`      | Libellé complet brut (utile pour debug)                          |
| `dimension`        | Format `LARGEUR/SERIERDIAM`, ex `205/55R16`                      |
| `load_index`       | Indice de charge (ex `91`)                                       |
| `speed_index`      | Indice de vitesse (ex `W`)                                       |
| `season`           | `summer` / `winter` / `4s` / `null`                              |
| `runflat`          | `true` si Run-Flat                                               |
| `tier`             | Code gamme : `premium` / `moyenne_gamme` / `premier_prix` (toujours renseigné) |
| `tier_label`       | Libellé gamme prêt à lire à l'oral : `Premium` / `Moyenne Gamme` / `Premier Prix` |
| `labels.fuel_efficiency` | Classe étiquette UE conso (A-E) ou `null`                  |
| `labels.wet_grip`        | Classe étiquette UE adhérence sur sol mouillé (A-E)        |
| `labels.noise_db`        | Bruit en dB ou `null`                                      |
| `price_ttc`        | Prix de vente TTC en euros (peut être `null` si pas encore tarifé) |
| `promo`            | `null` si aucune promo active, sinon objet avec prix TTC promo   |
| `in_stock`         | `true` si quantité > 0 en stock                                  |
| `stock_qty`        | Quantité totale tous dépôts confondus                            |

### 3.6 Ordre de tri

Les résultats sont triés ainsi :

1. Articles **en stock** d'abord (puis articles hors stock, si `in_stock_only=false`)
2. **Prix TTC croissant** (du moins cher au plus cher)

C'est l'ordre attendu par défaut pour un agent téléphonique : présenter
d'abord le prix le plus accessible.

---

## 4. Endpoint : liste des marques

```
GET /api/v1/brands
```

Retourne la liste de toutes les marques distinctes présentes dans le
catalogue, avec leur gamme (tier) et le nombre d'articles. Utile pour
diagnostiquer les marques non classifiées.

**Exemple :**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.jumbopneus.shop/api/v1/brands"
```

**Réponse :**

```json
{
  "count": 24,
  "brands": [
    {
      "brand_code": "MICH",
      "brand_name": "Michelin",
      "tier": "premium",
      "tier_label": "Premium",
      "article_count": 612
    },
    {
      "brand_code": "KUMH",
      "brand_name": "Kumho",
      "tier": "moyenne_gamme",
      "tier_label": "Moyenne Gamme",
      "article_count": 287
    }
  ]
}
```

---

## 5. Endpoint : santé

```
GET /api/v1/health
```

Vérifie le token et la connexion à la base. Réponse :

```json
{ "status": "ok" }
```

À utiliser pour les health-checks de votre côté.

---

## 6. Codes d'erreur

| Code | Cas                                                              |
| ---- | ---------------------------------------------------------------- |
| 400  | Aucun critère fourni                                             |
| 401  | Token manquant ou invalide                                       |
| 500  | Erreur base de données                                           |
| 503  | Service indisponible (token serveur non configuré, BDD KO)       |

---

## 7. Recommandations d'intégration

- **Toujours envoyer la dimension complète** quand vous l'avez : la
  combinaison `width + aspect + diameter` réduit drastiquement le nombre de
  résultats et l'incertitude lue au client.
- **Cache côté client** : nos prix bougent rarement intraday. Vous pouvez
  cacher les réponses 5–15 minutes sans risque significatif.
- **Stock en temps réel** : la disponibilité (`in_stock`, `stock_qty`)
  reflète l'état de notre ERP au moment de la requête. Pour des décisions
  d'engagement (réservation, vente), interroger en fin d'appel pour
  reconfirmer.
- **Limite de débit** : pas de hard limit imposé pour l'instant, merci de
  rester en dessous de ~5 requêtes/seconde. Au-delà, contactez-nous pour
  dimensionner.

---

## 8. Évolutions prévues (non encore exposées)

Sur demande nous pouvons ajouter :

- Recherche par véhicule (marque/modèle/année → dimensions homologuées)
- Endpoint de prise de rendez-vous montage
- Webhook de mise à jour de stock

Nous contacter pour discuter de vos besoins.
