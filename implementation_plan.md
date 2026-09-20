# Plan d'Architecture — API FastAPI Sécurisée par Token (`ai-orchestration`)

Ce plan décrit la création d'une **API REST FastAPI sécurisée par un Token secret** (`Bearer Token`). Ce service tournera en arrière-plan sur votre VPS (via PM2 ou systemd) et sera interrogé directement par votre application Next.js existante sur votre route protégée `/demo`.

---

## User Review Required

> [!IMPORTANT]
> **Intégration Next.js + API Python :**
> * L'application Python `ai-orchestration` expose uniquement l'API HTTP sécurisée.
> * Votre application Next.js existante (déjà déployée) appellera cette API depuis la page d'administration `/demo`.
> * L'accès à l'API Python est protégé par un Token secret configurable (`ORCHESTRATION_BEARER_TOKEN`).

---

## Architecture Proposée

```text
[Manager (Navigateur)]
       │
       ▼ (Connexion Admin)
[Projet Next.js (Page /demo)]
       │
       ▼ (Appel API HTTP interne avec Bearer Token)
[Nginx (Reverse Proxy)]
       │
       ▼ (Port local 8000)
[PM2 / Uvicorn]
       │
       ▼
[FastAPI Service (`src/ai_orchestration/server.py`)]
       │
       ▼
[Workflow LangGraph (Jumbo Pneus + Groq)]
```

---

## 1. Composants à Implémenter

### Serveur FastAPI Sécurisé ([`src/ai_orchestration/server.py`](file:///Users/ayouba/Documents/jumbo/ai-stuff/src/ai_orchestration/server.py))

* **Authentification par Token :** Vérification du header `Authorization: Bearer <ORCHESTRATION_BEARER_TOKEN>`. Retourne un code `401 Unauthorized` si le token est invalide ou absent.
* **Endpoint `POST /api/v1/chat` :**
  * *Entrée :* `{"message": "Je cherche du 205/55R16 Michelin"}`
  * *Sortie :* `{"response": "...", "status": "success", "error": null}`
* **Endpoint `GET /health` :** Test de santé accessible sans authentification pour Nginx / PM2.

### Configuration PM2 & Systemd

Fichier `ecosystem.config.js` pour la gestion du processus par PM2 sur le VPS :
```javascript
module.exports = {
  apps: [{
    name: 'jumbo-ai-api',
    script: 'uv',
    args: 'run uvicorn ai_orchestration.server:app --host 127.0.0.1 --port 8000',
    cwd: './',
    env: {
      NODE_ENV: 'production',
    }
  }]
};
```

### Directives Nginx Reverse Proxy (Exemple pour le VPS)

```nginx
location /orchestration/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## Plan de Vérification

### Tests Automatisés
* Ajout de `fastapi` et `uvicorn` dans `pyproject.toml`.
* Test unitaire `tests/test_server.py` :
  * Test de rejet sans Token (HTTP 401).
  * Test d'acceptation avec Token valide (HTTP 200).
  * Test de réponse de santé `/health`.

### Vérification Manuelle
* Test via cURL avec le Bearer token :
  ```bash
  curl -H "Authorization: Bearer SECRET_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"message":"205/55R16"}' \
       http://127.0.0.1:8000/api/v1/chat
  ```
