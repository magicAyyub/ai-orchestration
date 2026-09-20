"""Serveur HTTP FastAPI sécurisé par Token Secret pour l'orchestration IA."""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

from ai_orchestration.config import settings
from ai_orchestration.graph import create_workflow
from ai_orchestration.api.client import JumboPneusClient
from ai_orchestration.observability import setup_observability, logger

setup_observability()

app = FastAPI(
    title="Jumbo Pneus AI Orchestration API",
    description="API REST d'orchestration contrôlée pour la recherche et le conseil en pneumatiques.",
    version="0.1.0",
)

security = HTTPBearer()


class ChatRequest(BaseModel):
    """Schéma du corps de la requête de chat."""
    message: str = Field(..., description="Message ou question de l'utilisateur")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None, description="Historique optionnel sous forme de liste [{'role': 'user'|'assistant', 'content': '...'}]"
    )


class ChatResponse(BaseModel):
    """Schéma de réponse du serveur de chat."""
    response: str
    escalated_to_human: bool = False
    status: str = "success"


def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Vérifie la validité du Token Bearer transmis dans l'en-tête Authorization."""
    expected_token = settings.jumbo_api_key
    if not credentials or credentials.credentials != expected_token:
        logger.warning("Tentative d'accès API avec un Token Bearer invalide ou absent.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification invalide ou absent.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@app.get("/health")
def health_check():
    """Endpoint de santé public pour PM2 et Nginx."""
    client = JumboPneusClient()
    try:
        api_health = client.check_health()
        return {"status": "ok", "jumbo_api": api_health.get("status", "ok")}
    except Exception as e:
        logger.error(f"Échec de la vérification de santé dans l'API: {e}")
        return {"status": "degraded", "detail": str(e)}


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    token: str = Depends(verify_bearer_token),
):
    """Endpoint sécurisé d'exécution du graphe d'agent LangGraph."""
    graph_app = create_workflow()
    messages = []

    if request.conversation_history:
        for item in request.conversation_history:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=request.message))
    
    try:
        result = graph_app.invoke({"messages": messages})
        last_message = result["messages"][-1]
        is_escalated = result.get("escalated_to_human", False)

        return ChatResponse(
            response=last_message.content,
            escalated_to_human=is_escalated,
            status="success",
        )
    except Exception as e:
        logger.error(f"Erreur d'exécution dans le graphe d'agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement de la requête: {str(e)}",
        )
