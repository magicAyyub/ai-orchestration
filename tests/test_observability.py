"""Tests unitaires pour le handler de télémesure LangChain."""
import uuid
from ai_orchestration.observability import JumboTelemetryCallbackHandler


def test_telemetry_callback_handler_events():
    """Vérifie le suivi du cycle de vie des outils par le handler de télémesure."""
    handler = JumboTelemetryCallbackHandler()
    run_id = uuid.uuid4()

    handler.on_tool_start({"name": "search_tires"}, '{"width": 205}', run_id=run_id)
    assert str(run_id) in handler._tool_start_times

    handler.on_tool_end({"items": []}, run_id=run_id)
    assert str(run_id) not in handler._tool_start_times
