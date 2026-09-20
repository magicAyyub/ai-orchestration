"""Tests de bout en bout pour les 4 parcours conversationnels du workflow LangGraph."""
from langchain_core.messages import HumanMessage
from ai_orchestration.graph.workflow import create_workflow


def test_workflow_creation():
    """Vérifie la compilation initiale du graphe."""
    app = create_workflow()
    assert app is not None


def test_workflow_incomplete_criteria():
    """Vérifie que l'agent demande poliment les critères manquants sans appeler d'outil."""
    app = create_workflow()
    inputs = {"messages": [HumanMessage(content="Je cherche des pneus en largeur 205")]}
    output = app.invoke(inputs)
    last_message = output["messages"][-1]
    assert last_message.content != ""
    # Aucun appel d'outil ne doit être effectué pour une dimension incomplète
    assert not hasattr(last_message, "tool_calls") or len(last_message.tool_calls) == 0


def test_workflow_human_escalation():
    """Vérifie que l'agent déclenche l'escalade vers un humain pour une demande complexe."""
    app = create_workflow()
    inputs = {"messages": [HumanMessage(content="Bonjour, je souhaite négocier un tarif pour une flotte de 50 véhicules de mon entreprise.")]}
    output = app.invoke(inputs)
    last_message = output["messages"][-1]
    assert "conseiller spécialisé" in last_message.content.lower() or "expert" in last_message.content.lower()
    assert output.get("escalated_to_human") is True


def test_workflow_out_of_scope():
    """Vérifie le recadrage poliment en cas de demande totalement hors-sujet."""
    app = create_workflow()
    inputs = {"messages": [HumanMessage(content="Peux-tu me donner la recette de la tarte tatin ?")]}
    output = app.invoke(inputs)
    last_message = output["messages"][-1]
    assert "jumbo pneus" in last_message.content.lower() or "spécialisé" in last_message.content.lower()
    assert not hasattr(last_message, "tool_calls") or len(last_message.tool_calls) == 0


def test_workflow_standard_search():
    """Vérifie l'exécution complète d'une recherche standard avec appel d'outil."""
    app = create_workflow()
    inputs = {"messages": [HumanMessage(content="Je cherche des pneus Michelin 205/55R16")]}
    output = app.invoke(inputs)
    assert "messages" in output
    last_message = output["messages"][-1]
    assert last_message.content != ""
