# Jumbo Pneus Partner API — Reference

**Version:** v1
**Last updated:** 2026-05-30
**Maintainer:** cheng@jumbopneus.fr

---

## Table of Contents

1. [Overview](#1-overview)
2. [Base URL & Environments](#2-base-url--environments)
3. [Authentication](#3-authentication)
4. [Rate Limits & Quotas](#4-rate-limits--quotas)
5. [Endpoints](#5-endpoints)
   - 5.1 [`GET /api/v1/health`](#51-get-apiv1health)
   - 5.2 [`GET /api/v1/tire-search`](#52-get-apiv1tire-search)
   - 5.3 [`GET /api/v1/brands`](#53-get-apiv1brands)
6. [Data Schemas](#6-data-schemas)
7. [Tier Classification (Premium / Moyenne Gamme / Premier Prix)](#7-tier-classification)
8. [Filtering, Sorting & Pagination](#8-filtering-sorting--pagination)
9. [HTTP Status Codes & Error Format](#9-http-status-codes--error-format)
10. [Code Examples](#10-code-examples)
11. [Integration Guidelines](#11-integration-guidelines)
12. [Versioning & Changelog](#12-versioning--changelog)
13. [Support](#13-support)

---

## 1. Overview

The Jumbo Pneus Partner API is a read-only HTTP/JSON service that exposes
the Jumbo Pneus tire catalogue and live stock to authorized partners. It is
designed for integrations such as AI phone receptionists, comparator
websites, B2B catalog mirrors and order intake systems.

Each query returns the following business attributes for matched tires:

- Brand (commercial name + internal code)
- Model and tire designation
- Dimension (width / aspect / diameter / load index / speed index)
- Season classification (`summer` / `winter` / `4s`)
- Tier classification (`premium` / `moyenne_gamme` / `premier_prix`)
- Run-flat flag
- EU label (fuel efficiency, wet grip, noise dB)
- Live retail price (TTC, EUR)
- Active promotional price (if any)
- Stock availability (boolean + quantity)

The API **does not** expose internal financial data such as purchase price,
last cost, margin, or dormant-stock flags. These are deliberately stripped
from responses.

---

## 2. Base URL & Environments

| Environment | Base URL                          | Notes                                |
| ----------- | --------------------------------- | ------------------------------------ |
| Production  | `https://api.jumbopneus.shop`     | Public, served via Cloudflare        |
| Internal    | `http://<host>:8001`              | Reserved for Jumbo Pneus operations  |

All endpoints in this document are relative to the **Base URL**. For
example, `GET /api/v1/health` resolves to
`https://api.jumbopneus.shop/api/v1/health` in production.

The production endpoint terminates TLS at Cloudflare. All requests must
use HTTPS. HTTP requests will be redirected or refused.

---

## 3. Authentication

The API uses **Bearer token authentication** over HTTPS. Every request
must include the following header:

```
Authorization: Bearer <PARTNER_API_TOKEN>
```

### Token issuance

Tokens are issued to partners out-of-band (encrypted email, signed PGP,
or direct exchange). Each partner receives a **dedicated token**:

- Independent of internal Jumbo Pneus tokens.
- Revocable on demand without impacting other systems.
- Trackable per partner for usage analytics.

### Token handling rules

- Treat the token as a secret. Do not commit it to source control.
- Do not embed the token in client-side code or mobile apps.
- Store it in environment variables or a secrets manager.
- If a token is leaked, contact `cheng@jumbopneus.fr` immediately for
  rotation. Rotation takes effect within minutes.

### Failure modes

| HTTP code | Condition                                            |
| --------- | ---------------------------------------------------- |
| 401       | Missing, malformed, or unrecognized token            |
| 503       | Server-side token configuration is missing (incident)|

A 401 response also includes the standard
`WWW-Authenticate: Bearer` header.

---

## 4. Rate Limits & Quotas

There is currently no hard rate limit enforced at the application layer.
However, partners are expected to stay within:

- **5 requests per second** sustained
- **300 requests per minute** burst

If you anticipate higher traffic, contact us in advance so we can
provision additional capacity. Sustained abuse may trigger Cloudflare
WAF rules.

Recommended client behavior:

- Cache `/api/v1/brands` responses for at least 1 hour.
- Cache `/api/v1/tire-search` responses for 5–15 minutes per unique
  parameter set.
- Re-validate availability immediately before any commercial commitment.

---

## 5. Endpoints

### 5.1 `GET /api/v1/health`

Lightweight health check. Verifies authentication and database
connectivity.

**Authentication:** required.

**Request parameters:** none.

**Response (200):**

```json
{
  "status": "ok"
}
```

**Failure responses:**

| Code | Meaning                                |
| ---- | -------------------------------------- |
| 401  | Invalid or missing token               |
| 503  | Database unreachable                   |

---

### 5.2 `GET /api/v1/tire-search`

Search the tire catalogue and return live stock & pricing.

**Authentication:** required.

**At least one filter must be provided.** Acceptable filters: `ean`, any
of `width` / `aspect` / `diameter`, `brand`, `q`, or `tier`. A request
with no filters returns HTTP 400.

#### Request parameters

| Name            | Type    | In    | Default | Constraints   | Description                                                                |
| --------------- | ------- | ----- | ------- | ------------- | -------------------------------------------------------------------------- |
| `width`         | integer | query | —       | 100 ≤ n ≤ 400 | Tire width in mm. Example: `205`.                                          |
| `aspect`        | integer | query | —       | 20 ≤ n ≤ 90   | Aspect ratio (sidewall height %). Example: `55`.                           |
| `diameter`      | integer | query | —       | 10 ≤ n ≤ 30   | Rim diameter in inches. Example: `16`.                                     |
| `brand`         | string  | query | —       | —             | Brand code or commercial name. Case-insensitive. Example: `MICH`, `michelin`. |
| `q`             | string  | query | —       | —             | Free-text search against article designation and model.                    |
| `season`        | string  | query | —       | enum + aliases| `summer` / `winter` / `4s`. French aliases accepted (`ete`, `hiver`, `4saisons`). |
| `runflat`       | boolean | query | —       | —             | If `true`, return only Run-Flat tires.                                     |
| `tier`          | string  | query | —       | enum + aliases| `premium` / `moyenne_gamme` / `premier_prix`. French and English aliases accepted (see §7). |
| `ean`           | string  | query | —       | digits only   | EAN-13 barcode. Non-digits are stripped before lookup.                     |
| `in_stock_only` | boolean | query | `true`  | —             | If `true`, only items with stock > 0 are returned.                         |
| `limit`         | integer | query | `50`    | 1 ≤ n ≤ 100   | Maximum number of items in the response.                                   |

#### Response (200)

```json
{
  "count": 2,
  "items": [
    {
      "sku": "MIPRI4205551691W",
      "ean": "3528705349843",
      "brand": "Michelin",
      "brand_code": "MICH",
      "model": "PRIMACY 4",
      "designation": "PN MICH 205/55R16 91W PRIMACY 4",
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
        "label": "Promo Ete 2026",
        "id": "PROMO_ETE_2026"
      },
      "in_stock": true,
      "stock_qty": 8
    }
  ],
  "filters": {
    "width": 205,
    "aspect": 55,
    "diameter": 16,
    "brand": null,
    "q": null,
    "season": null,
    "runflat": null,
    "tier": null,
    "ean": null,
    "in_stock_only": true
  }
}
```

The `filters` object echoes the effective (normalized) values used for
the query — useful for debugging.

#### Failure responses

| Code | Meaning                                              |
| ---- | ---------------------------------------------------- |
| 400  | No filter provided, or invalid `tier` value          |
| 401  | Invalid or missing token                             |
| 500  | Database error                                       |

---

### 5.3 `GET /api/v1/brands`

Returns the list of distinct brands present in the active tire
catalogue, with their current tier classification and the number of
articles per brand.

Primary use case: integration debugging — confirm that the partner's
classification matches what is being served, identify brand codes whose
articles end up in `premier_prix` by default.

**Authentication:** required.

**Request parameters:** none.

#### Response (200)

```json
{
  "count": 230,
  "brands": [
    {
      "brand_code": "CONT",
      "brand_name": "Continental",
      "tier": "premium",
      "tier_label": "Premium",
      "article_count": 7809
    },
    {
      "brand_code": "MICH",
      "brand_name": "Michelin",
      "tier": "premium",
      "tier_label": "Premium",
      "article_count": 6902
    }
  ]
}
```

Brands are ordered by `article_count` descending.

#### Failure responses

| Code | Meaning                                              |
| ---- | ---------------------------------------------------- |
| 401  | Invalid or missing token                             |
| 500  | Database error                                       |

---

## 6. Data Schemas

### 6.1 `TireItem`

| Field             | Type             | Nullable | Description                                                |
| ----------------- | ---------------- | -------- | ---------------------------------------------------------- |
| `sku`             | string           | no       | Internal Jumbo Pneus SKU (`c_art`). Stable identifier.     |
| `ean`             | string \| null   | yes      | EAN-13 barcode, digits only. `null` if not registered.     |
| `brand`           | string           | no       | Commercial brand name (e.g. `Michelin`).                   |
| `brand_code`      | string           | no       | Internal 2–4 letter brand code (e.g. `MICH`).              |
| `model`           | string \| null   | yes      | Cleaned model name (e.g. `PRIMACY 4`).                     |
| `designation`     | string \| null   | yes      | Full internal label (rarely useful for end users).         |
| `dimension`       | string \| null   | yes      | Canonical dimension `WIDTH/ASPECTRDIAMETER` (e.g. `205/55R16`). |
| `width`           | integer \| null  | yes      | Width in mm.                                               |
| `aspect_ratio`    | integer \| null  | yes      | Aspect ratio.                                              |
| `diameter`        | integer \| null  | yes      | Rim diameter (inches).                                     |
| `load_index`      | string \| null   | yes      | Load index (e.g. `91`).                                    |
| `speed_index`     | string \| null   | yes      | Speed index (e.g. `W`).                                    |
| `season`          | string \| null   | yes      | `summer` / `winter` / `4s` or `null`.                      |
| `runflat`         | boolean          | no       | `true` if Run-Flat.                                        |
| `tier`            | string           | no       | `premium` / `moyenne_gamme` / `premier_prix`. Never null.  |
| `tier_label`      | string           | no       | Display label for the tier (e.g. `Moyenne Gamme`).         |
| `labels`          | `LabelObject`    | no       | EU tire label data. See 6.2.                               |
| `price_ttc`       | number \| null   | yes      | Retail price including VAT, EUR. May be `null` if not priced. |
| `promo`           | `PromoObject` \| null | yes | Active promotional price, or `null` if none.               |
| `in_stock`        | boolean          | no       | `true` if total stock > 0.                                 |
| `stock_qty`       | integer          | no       | Total stock across depots.                                 |

### 6.2 `LabelObject`

| Field             | Type             | Nullable | Description                                                |
| ----------------- | ---------------- | -------- | ---------------------------------------------------------- |
| `fuel_efficiency` | string \| null   | yes      | EU fuel efficiency class: `A`–`E` or `null`.               |
| `wet_grip`        | string \| null   | yes      | EU wet grip class: `A`–`E` or `null`.                      |
| `noise_db`        | integer \| null  | yes      | Drive-by noise in decibels.                                |

### 6.3 `PromoObject`

| Field        | Type             | Nullable | Description                                |
| ------------ | ---------------- | -------- | ------------------------------------------ |
| `price_ttc`  | number           | no       | Promotional price including VAT, EUR.      |
| `label`      | string \| null   | yes      | Human-readable promotion name.             |
| `id`         | string \| null   | yes      | Internal promotion identifier.             |

### 6.4 `BrandItem`

| Field            | Type    | Nullable | Description                                                 |
| ---------------- | ------- | -------- | ----------------------------------------------------------- |
| `brand_code`     | string  | no       | Internal brand code.                                        |
| `brand_name`     | string  | no       | Commercial brand name.                                      |
| `tier`           | string  | no       | `premium` / `moyenne_gamme` / `premier_prix`.               |
| `tier_label`     | string  | no       | Display label for the tier.                                 |
| `article_count`  | integer | no       | Number of tire SKUs from this brand in the active catalogue. |

---

## 7. Tier Classification

Every tire returned by the API carries a `tier` field. There are three
possible values:

| `tier`           | `tier_label`     | Brands (production state, 2026-05-30)                                                                                                  |
| ---------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `premium`        | `Premium`        | Michelin, Continental, Bridgestone, Pirelli, Goodyear, Dunlop, Hankook                                                                 |
| `moyenne_gamme`  | `Moyenne Gamme`  | Kumho, Yokohama, Nokian, Falken, Nexen, Vredestein, Toyo, BF Goodrich, Kleber, Uniroyal, Firestone, GT-Radial, Nankang                 |
| `premier_prix`   | `Premier Prix`   | All other brands (default fallback). Includes sub-brands such as Fulda, Kormoran, Sava, Matador, Barum, Semperit, Lassa, Cooper, etc. |

Rule: `tier` is computed from the article's `brand_code`. Any brand not
explicitly listed as Premium or Moyenne Gamme is automatically
classified as Premier Prix. The list is maintained server-side and is
visible at `GET /api/v1/brands`.

### Tier filter input — accepted aliases

When sending `?tier=...`, the API normalizes the value (case- and
whitespace-insensitive). Accepted inputs:

| Canonical value  | Accepted aliases                                                                  |
| ---------------- | --------------------------------------------------------------------------------- |
| `premium`        | `premium`, `haut`, `haut de gamme`, `haut_de_gamme`, `hdg`                        |
| `moyenne_gamme`  | `moyenne_gamme`, `moyenne-gamme`, `moyenne gamme`, `moyenne`, `quality`, `mid`, `mid_range`, `mid-range`, `milieu de gamme` |
| `premier_prix`   | `premier_prix`, `premier-prix`, `premier prix`, `pp`, `budget`, `entree_de_gamme`, `entree de gamme`, `edg` |

Any other value yields HTTP 400.

---

## 8. Filtering, Sorting & Pagination

### Filters

Filters are combined with logical AND. A request matches a tire only if
**all** provided filters match.

The combination `width=X&aspect=Y&diameter=Z` is the most selective and
should be used whenever the customer has stated the dimension explicitly.

### Sorting

Results are sorted as follows (deterministic):

1. In-stock items first (`in_stock = true`), out-of-stock items after.
2. Within each stock bucket, `price_ttc` ascending (cheapest first).
3. Items without a price (`price_ttc = null`) are sorted last.

This ordering is optimal for a phone agent that wants to present the
cheapest available option first.

### Pagination

The current version does not support cursor or offset pagination. Use
the `limit` parameter (max 100). For larger result sets, narrow the
search with more filters (e.g. add `brand` or `tier`).

---

## 9. HTTP Status Codes & Error Format

### Status code summary

| Code | Meaning                                                       |
| ---- | ------------------------------------------------------------- |
| 200  | Success                                                       |
| 400  | Bad request (missing filters, invalid `tier`, etc.)           |
| 401  | Unauthorized (missing, malformed, or invalid token)           |
| 404  | Not found (only returned by some legacy endpoints; not by v1) |
| 500  | Internal server error (database failure or similar)           |
| 503  | Service unavailable (server token misconfigured, DB down)     |

### Error response shape

All errors follow the FastAPI convention:

```json
{
  "detail": "Provide at least one filter: ean, width/aspect/diameter, brand, q, or tier."
}
```

For 401 responses, the body is:

```json
{
  "detail": "Invalid partner token"
}
```

with the additional response header `WWW-Authenticate: Bearer`.

---

## 10. Code Examples

### 10.1 cURL

```bash
# Health check
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.jumbopneus.shop/api/v1/health"

# Search by dimension, premium tier only
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.jumbopneus.shop/api/v1/tire-search?width=205&aspect=55&diameter=16&tier=premium&limit=5"

# Lookup by EAN
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.jumbopneus.shop/api/v1/tire-search?ean=3528705349843"

# List all brands
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.jumbopneus.shop/api/v1/brands"
```

### 10.2 Python (requests)

```python
import os
import requests

BASE = "https://api.jumbopneus.shop/api/v1"
TOKEN = os.environ["JUMBO_API_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def search_tires(width: int, aspect: int, diameter: int, tier: str | None = None,
                 limit: int = 10) -> dict:
    params = {
        "width": width,
        "aspect": aspect,
        "diameter": diameter,
        "limit": limit,
    }
    if tier:
        params["tier"] = tier
    r = requests.get(f"{BASE}/tire-search", params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


result = search_tires(205, 55, 16, tier="premium", limit=3)
for item in result["items"]:
    print(f"{item['brand']:12} {item['model']:20} {item['price_ttc']:>7.2f}EUR  stock={item['stock_qty']}")
```

### 10.3 JavaScript (fetch)

```javascript
const BASE = "https://api.jumbopneus.shop/api/v1";
const TOKEN = process.env.JUMBO_API_TOKEN;

async function searchTires({ width, aspect, diameter, tier, limit = 10 }) {
  const params = new URLSearchParams({ width, aspect, diameter, limit });
  if (tier) params.set("tier", tier);

  const res = await fetch(`${BASE}/tire-search?${params}`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

const result = await searchTires({
  width: 205, aspect: 55, diameter: 16, tier: "moyenne_gamme", limit: 5,
});
console.table(result.items.map(i => ({
  brand: i.brand, model: i.model, price: i.price_ttc, stock: i.stock_qty,
})));
```

### 10.4 PHP

```php
<?php
$BASE = 'https://api.jumbopneus.shop/api/v1';
$TOKEN = getenv('JUMBO_API_TOKEN');

function search_tires(array $params): array {
    global $BASE, $TOKEN;
    $url = $BASE . '/tire-search?' . http_build_query($params);
    $ctx = stream_context_create([
        'http' => [
            'method' => 'GET',
            'header' => "Authorization: Bearer $TOKEN\r\n",
            'timeout' => 10,
        ],
    ]);
    $body = file_get_contents($url, false, $ctx);
    return json_decode($body, true);
}

$result = search_tires([
    'width' => 205, 'aspect' => 55, 'diameter' => 16,
    'tier' => 'premier_prix', 'limit' => 5,
]);
foreach ($result['items'] as $item) {
    printf("%-12s %-20s %7.2f EUR  stock=%d\n",
        $item['brand'], $item['model'], $item['price_ttc'], $item['stock_qty']);
}
```

---

## 11. Integration Guidelines

### When to call which endpoint

| Customer intent (phone)                        | Recommended call                                                                   |
| ---------------------------------------------- | ---------------------------------------------------------------------------------- |
| "I drive a Clio, 205/55 R16, what do you have?"| `tire-search?width=205&aspect=55&diameter=16`                                       |
| "Do you have Michelin Primacy in 205/55R16?"   | `tire-search?width=205&aspect=55&diameter=16&brand=MICH&q=primacy`                  |
| "I want a premium tire for 205/55R16"          | `tire-search?width=205&aspect=55&diameter=16&tier=premium`                          |
| "Give me the cheapest premier prix in 205/55R16"| `tire-search?width=205&aspect=55&diameter=16&tier=premier_prix&limit=1`            |
| "I need a winter tire in 235/55R18"            | `tire-search?width=235&aspect=55&diameter=18&season=winter`                         |
| "Here's the barcode: 3528705349843"            | `tire-search?ean=3528705349843`                                                     |

### Caching guidance

| Resource              | TTL recommendation | Reason                                              |
| --------------------- | ------------------ | --------------------------------------------------- |
| `/brands`             | 1 hour             | Brand list changes rarely.                          |
| `/tire-search`        | 5–15 minutes       | Prices rarely change intraday; stock can move.      |
| Stock for commitment  | Live (no cache)    | Re-fetch before any reservation or order intake.    |

### Idempotency & retries

All endpoints are GET and idempotent. Retry on transient `5xx` errors
with exponential backoff (initial 500 ms, factor 2, max 5 retries).

### Recommended client headers

```
User-Agent: <YourProductName>/<Version> (contact: ops@yourcompany.com)
Accept: application/json
```

A descriptive `User-Agent` helps us identify your traffic if we need to
contact you about anomalies.

---

## 12. Versioning & Changelog

The API uses URL versioning. The current version is **v1**, served
under `/api/v1/...`. Breaking changes will be introduced under a new
version path (`/api/v2/...`), and the previous version will remain
operational for at least 6 months after the new version is released.

### Changelog

| Version | Date       | Changes                                                                  |
| ------- | ---------- | ------------------------------------------------------------------------ |
| 1.1.0   | 2026-05-30 | Added `tier` and `tier_label` fields. Added `tier` query parameter. Added `/api/v1/brands` endpoint. Default sort changed to `price_ttc` ascending. |
| 1.0.0   | 2026-05-29 | Initial release. `/api/v1/tire-search` and `/api/v1/health`.            |

---

## 13. Support

- **Functional questions, integration help, token issuance & rotation:**
  cheng@jumbopneus.fr
- **Incident reports & production issues:** same email, mention `[INCIDENT]`
  in the subject. Acknowledged within 24h business hours.
- **Security disclosures:** same email, mention `[SECURITY]` in the
  subject. Please do not disclose publicly until we have responded.

---

*End of document.*
