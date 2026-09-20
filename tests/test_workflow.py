"""Tests de bout en bout pour le workflow LangGraph."""
from langchain_core.messages import HumanMessage
from ai_orchestration.graph.workflow import create_workflow


def test_workflow_creation():
    """Vérifie la compilation initiale du graphe."""
    app = create_workflow()
    assert app is not None


def test_workflow_execution():
    """Vérifie l'exécution complète d'une requête dans le graphe."""
    app = create_workflow()
    inputs = {"messages": [HumanMessage(content="Bonjour, cherchez-vous des pneus Michelin en 205/55R16 ?")]}
    output = app.invoke(inputs)
    assert "messages" in output
    assert len(output["messages"]) > 1
    last_message = output["messages"][-1]
    assert last_message.content != ""
