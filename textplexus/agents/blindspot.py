import uuid
from textplexus.schemas import CampaignState, Evidence, SpecialistOutput
from textplexus.config import Config, get_llm

llm = get_llm()

async def blindspot_node(state: CampaignState):
    """
    BlindSpot Agent: Surfaces possibilities humans forget (inversion, second-order effects, black swans).
    """
    focus_id = state.current_focus_id
    if not focus_id:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    
    prompt = f"""You are the BlindSpot Agent. Identify overlooked factors for the current hypothesis.
    Think about: inversion, pre-mortems, second-order effects, black swans, incentive misalignments.
    
    Research Query: {state.query}
    Current Hypothesis Branch: {hypothesis.content}
    
    Provide structured JSON with 'evidence' (the blindspot discovered) and 'impact_on_probability'.
    """
    
    result = await llm.with_structured_output(SpecialistOutput).ainvoke(prompt)
    
    e_id = str(uuid.uuid4())[:8]
    evidence = Evidence(
        id=e_id,
        hypothesis_id=focus_id,
        source="BlindSpot Analysis",
        content=result.evidence
    )
    state.evidence.append(evidence)
    
    return state
