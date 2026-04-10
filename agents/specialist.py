import uuid
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from ..schemas import CampaignState, SpecialistOutput, Evidence
from ..config import Config

llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, google_api_key=Config.GEMINI_API_KEY)

async def specialist_node(state: CampaignState):
    """
    Specialist Fleet: Dynamic parallel agents attacking from divergent angles.
    """
    focus_id = state.current_focus_id
    if not focus_id:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    
    angles = [
        "Data-driven analysis",
        "Historical precedents",
        "Skeptic/Red-team perspective",
        "Simulator/Monte-Carlo reasoning",
        "First-principles logic"
    ]
    
    tasks = []
    for angle in angles:
        tasks.append(run_specialist(angle, hypothesis.content, state.query))
    
    outputs = await asyncio.gather(*tasks)
    
    for out in outputs:
        e_id = str(uuid.uuid4())[:8]
        evidence = Evidence(
            id=e_id,
            hypothesis_id=focus_id,
            source=out.reasoning[:50],  # simplified source
            content=out.evidence
        )
        state.evidence.append(evidence)
        # Probabilities will be updated in the Aggregator node
        
    return state

async def run_specialist(angle: str, hypothesis: str, query: str) -> SpecialistOutput:
    prompt = f"""You are a Specialist Agent focusing on: {angle}.
    Research Query: {query}
    Current Hypothesis Branch: {hypothesis}
    
    Provide factual evidence and your estimation of how this evidence impacts the probability of this hypothesis being true.
    Impact should be between -1.0 (highly unlikely) and 1.0 (highly likely).
    """
    return await llm.with_structured_output(SpecialistOutput).ainvoke(prompt)
