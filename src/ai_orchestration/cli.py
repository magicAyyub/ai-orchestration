"""Interface en ligne de commande (CLI) Typer pour Jumbo Pneus."""
from typing import Optional
import typer
from langchain_core.messages import HumanMessage
from ai_orchestration.graph import create_workflow
from ai_orchestration.api.client import JumboPneusClient

app = typer.Typer(
    name="jumbo",
    help="CLI d'orchestration et de recherche pour l'API Jumbo Pneus.",
    add_completion=False,
)


@app.command(name="chat")
def chat_command():
    """Démarre une session de dialogue interactive avec l'assistant Jumbo Pneus."""
    typer.echo("Jumbo Pneus - Assistant Virtuel")
    typer.echo("Tapez exit ou quit pour quitter.\n")

    graph_app = create_workflow()
    messages = []

    while True:
        try:
            user_input = typer.prompt("Vous").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                typer.echo("Au revoir !")
                break

            messages.append(HumanMessage(content=user_input))
            result = graph_app.invoke({"messages": messages})
            
            messages = result["messages"]
            assistant_response = messages[-1].content
            typer.echo(f"\nAssistant Jumbo Pneus :\n{assistant_response}\n")
        except (KeyboardInterrupt, typer.Abort):
            typer.echo("\nAu revoir !")
            break
        except Exception as e:
            typer.echo(f"\nErreur : {e}\n")


@app.command(name="search")
def search_command(
    query: str = typer.Argument(..., help="Requête de recherche en langage naturel (ex: 205/55R16 Michelin)")
):
    """Exécute une recherche unique via l'agent IA."""
    graph_app = create_workflow()
    result = graph_app.invoke({"messages": [HumanMessage(content=query)]})
    assistant_response = result["messages"][-1].content
    typer.echo(assistant_response)


@app.command(name="health")
def health_command():
    """Vérifie l'état de santé de l'API Jumbo Pneus."""
    client = JumboPneusClient()
    try:
        res = client.check_health()
        typer.echo(f"Statut API: {res.get('status', 'inconnu')}")
    except Exception as e:
        typer.echo(f"Erreur API: {e}")


@app.command(name="brands")
def brands_command():
    """Affiche la liste des marques et leur classification de gamme."""
    client = JumboPneusClient()
    try:
        res = client.get_brands()
        typer.echo(f"Nombre total de marques: {res.count}")
        for brand in res.brands:
            typer.echo(f"* {brand.brand_name} ({brand.brand_code}) - Gamme: {brand.tier_label} - SKUs: {brand.article_count}")
    except Exception as e:
        typer.echo(f"Erreur API: {e}")


if __name__ == "__main__":
    app()
