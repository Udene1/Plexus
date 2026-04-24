import uuid
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from textplexus.schemas import CampaignState, SpecialistOutput, Evidence
from textplexus.config import Config
from textplexus.tools import web_search

llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, google_api_key=Config.GEMINI_API_KEY)

async def specialist_node(state: CampaignState):
    """
    Specialist Fleet: Consolidated high-efficiency analysis.
    Uses a single LLM call for multiple divergent angles to respect strict free-tier quotas.
    """
    focus_id = state.current_focus_id
    if not focus_id:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    
    # Perform a single broad search for the consolidated prompt
    search_query = f"evidence and data for {hypothesis.content} predictions 2028 batteries"
    print(f"--- Performing Grounding Search ---")
    search_results = web_search(search_query)
    search_context = "\n".join([f"- {r['title']}: {r['body']}" for r in search_results])
    
    prompt = f"""You are the Plexus Specialist Fleet. Analyze the following hypothesis from 5 divergent angles:
    1. Data-driven/Statistics
    2. Historical Precedents
    3. Skeptic/Red-team Perspective
    4. Probabilistic/Monte-Carlo reasoning
    5. First-principles logic
    
    Hypothesis: {hypothesis.content}
    Original Query: {state.query}
    
    Web Grounding Context:
    {search_context}
    
    For EACH angle, provide a concise evidence block.
    Return your response as a list of 5 evidence items.
    """
    
    print(f"--- Running Consolidated Specialist Fleet ---")
    # Using a structured or formatted list response
    # For simplicity in this refactor, we'll ask for a specific format and parse it
    response = await llm.ainvoke(prompt)
    
    # Simple split-based parsing for the consolidated response
    content = response.content
    sections = content.split("Angle:") if "Angle:" in content else content.split("\n\n")
    
    angles = ["Data", "History", "Skeptic", "Probabilistic", "Logic"]
    for i, section in enumerate(sections[:5]):
        if len(section.strip()) < 20: continue
        
        e_id = str(uuid.uuid4())[:8]
        angle_name = angles[i] if i < len(angles) else "General"
        evidence = Evidence(
            id=e_id,
            hypothesis_id=focus_id,
            source=f"Specialist ({angle_name})",
            content=section.strip()
        )
        state.evidence.append(evidence)
        
    return state

async def run_specialist(angle: str, search_query: str, hypothesis: str, query: str) -> SpecialistOutput:
    # Perform web search for grounding
    search_results = web_search(search_query, max_results=3)
    search_context = "\n".join([f"- {r['title']}: {r['body']} ({r['link']})" for r in search_results])
    
    prompt = f"""You are a Specialist Agent focusing on: {angle}.
    Research Query: {query}
    Current Hypothesis Branch: {hypothesis}
    
    WEB SEARCH CONTEXT:
    {search_context if search_results else "No search results found. Use your internal knowledge but cite it as 'Internal Reasoning'."}
    
    Based on the context above and your specialized angle, provide factual evidence and your estimation of how this evidence impacts the probability of this hypothesis being true.
    Impact should be between -1.0 (highly unlikely) and 1.0 (highly likely).
    """
    return await llm.with_structured_output(SpecialistOutput).ainvoke(prompt)
