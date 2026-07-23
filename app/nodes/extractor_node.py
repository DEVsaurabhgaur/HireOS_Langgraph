from app.schemas.pipeline_state import AgentState
from app.utils.sanitizers import sanitize_text

def extractor_node(state: AgentState) -> AgentState:
    clean_resume = sanitize_text(state.get('raw_resume', ''))
    state['parsed_sections'] = [{'title': 'Full Text', 'content': clean_resume}]
    state['current_step'] = 'extracted'
    return state
