# Orchestration d'Agent IA pour l'API Jumbo Pneus (`ai-orchestration`)

Ce projet implémente un système d'orchestration contrôlé et monitoré utilisant **LangGraph**, l’écosystème **LangChain**, le fournisseur LLM **Groq** et l'API Partenaire **Jumbo Pneus**.

## Architecture et Composants

Le projet est structuré sous forme de package Python moderne géré par `uv` :

* `src/ai_orchestration/api/` : Client HTTP `httpx` encapsulant l'API Jumbo Pneus avec typage Pydantic et gestion d'erreurs (401, 400, 500, 503).
* `src/ai_orchestration/schemas/` : Modèles Pydantic pour la validation des données d'entrée et de sortie.
* `src/ai_orchestration/tools/` : Outils LangChain (`@tool`) pour la recherche de pneus, l'extraction par code EAN et la consultation des marques.
* `src/ai_orchestration/graph/` : Workflow LangGraph (`StateGraph`) avec garde-fous métiers (stock minimal >= 2) et routing d'erreur d'infrastructure.
* `src/ai_orchestration/observability.py` : Télémesure basée sur `BaseCallbackHandler` de LangChain, intégration LangSmith et journalisation dans `logs/orchestration.log`.
* `src/ai_orchestration/cli.py` : Interface en ligne de commande Typer et raccourcis d'exécution (`jumbo`).

## Prérequis

* Python 3.9 ou supérieur
* Le gestionnaire de paquets `uv`

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

## Utilisation de la CLI (`jumbo`)

Exécuter une recherche rapide en une ligne :

```bash
uv run jumbo search "205/55R16 Michelin"
```

Lancer une session de chat interactive :

```bash
uv run jumbo chat
```

Tester la santé du service API :

```bash
uv run jumbo health
```

Consulter les marques disponibles et leurs gammes :

```bash
uv run jumbo brands
```

## Validation et Tests Automatisés

Lancer la suite complète de tests Pytest (client API, outils, workflow LangGraph, garde-fous et télémesure) :

```bash
uv run pytest
```

## Suivi des Logs et Observabilité

* Logs en direct dans le terminal : `tail -f logs/orchestration.log`
* Traces visuelles interactives : accessibles sur le tableau de bord LangSmith si `LANGCHAIN_TRACING_V2=true`.
