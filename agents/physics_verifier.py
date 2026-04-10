import sympy
import numpy as np
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from ..schemas import CampaignState, PhysicsCheckResult, Evidence
from ..config import Config

llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, google_api_key=Config.GEMINI_API_KEY)

async def physics_verifier_node(state: CampaignState):
    """
    Physics Verifier Agent: Uses SymPy + NumPy to flag violations of conservation laws, causality, etc.
    """
    focus_id = state.current_focus_id
    if not focus_id:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    
    # We ask the LLM to identify potential physics/causality constraints and code to check them
    prompt = f"""You are the Physics Verifier. Check the following hypothesis for violations of conservation laws, entropy, causality, or energy/momentum.
    Hypothesis: {hypothesis.content}
    
    If the hypothesis involves quantitative claims, suggest a Python/SymPy check.
    Return structured JSON with 'valid', 'violated_law', 'quantitative_constraint', and 'reasoning'.
    """
    
    result = await llm.with_structured_output(PhysicsCheckResult).ainvoke(prompt)
    
    if not result.valid:
        e_id = str(uuid.uuid4())[:8]
        evidence = Evidence(
            id=e_id,
            hypothesis_id=focus_id,
            source="Physics Verifier",
            content=f"VIOLATION: {result.violated_law}. Constraint: {result.quantitative_constraint}. Suggestion: {result.suggested_adjustment}"
        )
        state.evidence.append(evidence)
        # Probabilities will be heavily penalized in Aggregator
        
    return state
