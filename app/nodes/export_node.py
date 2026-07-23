from app.schemas.pipeline_state import AgentState

def export_node(state: AgentState) -> dict:
    return {'status': 'success', 'data': state}
