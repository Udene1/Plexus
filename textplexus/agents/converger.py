from langchain_google_genai import ChatGoogleGenerativeAI
from textplexus.schemas import CampaignState
from textplexus.config import Config

llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, google_api_key=Config.GEMINI_API_KEY)

async def converger_node(state: CampaignState):
    """
    Converger + Optimizer Agent: Synthesizes the final outcome and actionable paths.
    """
    if state.convergence_score < Config.CONVERGENCE_THRESHOLD and not state.is_finished:
        return state
        
    # Find winning hypotheses
    winners = [h for h in state.hypotheses.values() if h.probability > 0.5]
    winners.sort(key=lambda x: x.probability, reverse=True)
    
    prompt = f"""You are the Plexus Converger. Synthesize the 'last line' most-likely outcome for the research.
    
    Research Query: {state.query}
    Top Outcomes:
    {chr(10).join([f"- {h.content} (Prob: {h.probability:.2f})" for h in winners[:3]])}
    
    Provide:
    1. The tightest 'last line' outcome.
    2. Ranked actionable paths (steps, timelines, quick tests, risks).
    3. Final summary of evidence.
    """
    
    response = await llm.ainvoke(prompt)
    
    print("\n" + "#"*60)
    print("PLEXUS FINAL CONVERGENCE")
    print("#"*60)
    print(response.content)
    print("#"*60 + "\n")
    
    state.is_finished = True
    return state
