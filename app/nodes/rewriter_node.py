from app.schemas.pipeline_state import AgentState

def rewriter_node(state: AgentState) -> AgentState:
    state['rewritten_bullets'] = [{'original': 'Worked on API', 'rewritten': 'Architected high-throughput FastAPI service reducing latency by 35%'}]
    state['current_step'] = 'rewritten'
    return state
