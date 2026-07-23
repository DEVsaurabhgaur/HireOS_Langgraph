from app.schemas.pipeline_state import AgentState
from app.utils.score_calculator import calculate_weighted_ats_score

def analyzer_node(state: AgentState) -> AgentState:
    score = calculate_weighted_ats_score(85.0, 78.0, 90.0)
    state['ats_score'] = {'overall': score}
    state['current_step'] = 'analyzed'
    return state
