from app.schemas.pipeline_state import AgentState

def feedback_node(state: AgentState) -> AgentState:
    # Logs user feedback into optimization dataset
    return state
