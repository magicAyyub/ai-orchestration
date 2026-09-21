# Orchestration d'Agent IA pour l'API Jumbo Pneus (`ai-orchestration`)

Ce projet implémente un système d'orchestration contrôlé et monitoré utilisant **LangGraph**, l’écosystème **LangChain**, le fournisseur LLM **Groq** et l'API Partenaire **Jumbo Pneus**.

## Architecture et Composants

Le projet est structuré sous forme de package Python moderne géré par `uv` :

* `src/ai_orchestration/api/` : Client HTTP `httpx` encapsulant l'API Jumbo Pneus avec typage Pydantic et gestion d'erreurs (401, 400, 500, 503).
* `src/ai_orchestration/schemas/` : Modèles Pydantic pour la validation des données d'entrée et de sortie.
* `src/ai_orchestration/tools/` : Outils LangChain (`@tool`) pour la recherche de pneus, l'extraction par code EAN et la consultation des marques.
* `src/ai_orchestration/graph/` : Workflow LangGraph (`StateGraph`) avec garde-fous métiers (stock minimal >= 2) et routing d'erreur d'infrastructure.
* `src/ai_orchestration/observability.py` : Télémesure basée sur `BaseCallbackHandler` de LangChain, intégration LangSmith et journalisation dans `logs/orchestration.log`.
* `src/ai_orchestration/server.py` : Serveur API FastAPI sécurisé par Token Bearer.
* `src/ai_orchestration/cli.py` : Interface en ligne de commande Typer et raccourcis d'exécution (`jumbo`).

## Installation et Configuration

Installer le projet et ses dépendances :

```bash
uv sync
```

Copier et renseigner les clés d'API dans le fichier d'environnement :

```bash
cp .env.example .env
```

Variables requises dans `.env` :
* `JUMBO_API_KEY`: Clé d'accès à l'API Jumbo Pneus.
* `GROQ_API_KEY`: Clé d'accès à l'API Groq.

Variables optionnelles d'observabilité (LangSmith) :
* `LANGCHAIN_TRACING_V2=true`
* `LANGCHAIN_API_KEY=votre_cle_langsmith`
* `LANGCHAIN_PROJECT=jumbo-ai-orchestration`

## Procédure de Test en Local (Sur votre Mac)

### Test 1 : Validation de l’API FastAPI sécurisée

1. Démarrer le serveur HTTP en local sur le port 8000 avec le flag `--app-dir src` :
```bash
uv run uvicorn --app-dir src ai_orchestration.server:app --port 8000
```

2. Dans un second terminal, tester les requêtes cURL :

* Test de rejet sans Token (Retourne HTTP 401 Unauthorized) :
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Bonjour"}'
```

* Test d'une requête autorisée avec le Bearer Token :
```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
     -H "Authorization: Bearer LN4R2WJpvTSaX5bY" \
     -H "Content-Type: application/json" \
     -d '{"message": "Je cherche du 205/55R16 Michelin"}'
```

### Test 2 : Test des 4 parcours conversationnels via la CLI (`jumbo`)

* Parcours 1 (Critères incomplets) :
```bash
uv run jumbo search "Je cherche des pneus en 205"
```

* Parcours 2 (Escalade humain) :
```bash
uv run jumbo search "Je souhaite un devis pour une flotte de 50 camions"
```

* Parcours 3 (Recadrage hors-sujet) :
```bash
uv run jumbo search "Donne-moi la recette des crêpes"
```

* Parcours 4 (Recherche standard) :
```bash
uv run jumbo search "205/55R16 Michelin"
```

* Mode Chat interactif dans votre terminal :
```bash
uv run jumbo chat
```

### Test 3 : Suite de tests automatisés Pytest

Lancer la suite complète de tests :

```bash
uv run pytest
```

## Suivi des Logs et Observabilité

* Logs en direct dans le terminal : `tail -f logs/orchestration.log`
* Traces visuelles interactives : accessibles sur le tableau de bord LangSmith si `LANGCHAIN_TRACING_V2=true`.
