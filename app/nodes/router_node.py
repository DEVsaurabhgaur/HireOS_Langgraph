from app.schemas.pipeline_state import AgentState

def router_node(state: AgentState) -> str:
    if not state.get('parsed_sections'):
        return 'extractor'
    return 'analyzer'
