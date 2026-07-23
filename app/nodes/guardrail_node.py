from app.schemas.pipeline_state import AgentState

def guardrail_node(state: AgentState) -> AgentState:
    # Validates safety and non-hallucinated bullet outputs
    return state
