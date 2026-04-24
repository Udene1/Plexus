import sympy
import numpy as np
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from textplexus.schemas import CampaignState, PhysicsCheckResult, Evidence
from textplexus.config import Config

llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, google_api_key=Config.GEMINI_API_KEY)

async def physics_verifier_node(state: CampaignState):
    """
    Physics Verifier Agent: Uses SymPy + NumPy to flag violations.
    Now actually executes code to verify constraints.
    """
    focus_id = state.current_focus_id
    if not focus_id:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    
    prompt = f"""You are the Physics Verifier. Check the following hypothesis for violations of conservation laws, entropy, causality, or energy/momentum.
    Hypothesis: {hypothesis.content}
    
    If the hypothesis involves quantitative claims, provide exactly one block of Python code (using sympy as 'sp' or numpy as 'np') that calculates a result or checks a constraint.
    The code should set a variable 'is_valid' to True or False.
    
    Return structured JSON with 'valid', 'violated_law', 'quantitative_constraint', 'suggested_adjustment', and 'reasoning'.
    Store the python code in 'quantitative_constraint'.
    """
    
    result = await llm.with_structured_output(PhysicsCheckResult).ainvoke(prompt)
    
    # Attempt to execute the suggested code
    if result.quantitative_constraint and ("import" not in result.quantitative_constraint): # Basic safety check
        try:
            loc = {"sp": sympy, "np": np, "is_valid": True}
            exec(result.quantitative_constraint, {}, loc)
            if not loc["is_valid"]:
                result.valid = False
                result.reasoning += f"\nSandbox execution confirmed violation: {result.quantitative_constraint}"
        except Exception as e:
            print(f"Physics sandbox error: {e}")
            
    if not result.valid:
        e_id = str(uuid.uuid4())[:8]
        evidence = Evidence(
            id=e_id,
            hypothesis_id=focus_id,
            source="Physics Verifier (Sandbox)",
            content=f"VIOLATION: {result.violated_law}. Reason: {result.reasoning}. Suggestion: {result.suggested_adjustment}"
        )
        state.evidence.append(evidence)
        
    return state
