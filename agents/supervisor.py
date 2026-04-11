import uuid
import asyncio
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from ..schemas import CampaignState, Hypothesis, Decomposition
from ..config import Config

llm = ChatGoogleGenerativeAI(model=Config.MODEL_NAME, google_api_key=Config.GEMINI_API_KEY)

async def supervisor_node(state: CampaignState):
    """
    Supervisor Agent: Decomposes query into hypothesis branches or selects the next branch to deepen.
    """
    if not state.hypotheses:
        # Initial decomposition
        prompt = f"""You are the Plexus Supervisor. Decompose the following research query into {Config.BRANCH_COUNT} top-level, mutually exclusive hypothesis branches.
        Query: {state.query}
        
        Provide structured JSON output with 'hypotheses' (list of strings) and 'reasoning'.
        """
        for i in range(3):
            response = await llm.with_structured_output(Decomposition).ainvoke(prompt)
            if response:
                break
            print(f"Supervisor retry {i+1} due to empty response...")
            await asyncio.sleep(5)
            
        if not response:
            print("Error: Supervisor failed after retries. Using fallback hypothesis.")
            h_id = "fallback"
            state.hypotheses[h_id] = Hypothesis(id=h_id, content="General research on " + state.query, depth=0, probability=1.0)
            state.current_focus_id = h_id
            return state
            
        new_hypotheses = {}
        for h_content in response.hypotheses:
            h_id = str(uuid.uuid4())[:8]
            new_hypotheses[h_id] = Hypothesis(
                id=h_id,
                content=h_content,
                depth=0,
                probability=1.0 / len(response.hypotheses)
            )
        
        state.hypotheses.update(new_hypotheses)
        state.iteration += 1
        # Set first focus
        state.current_focus_id = list(new_hypotheses.keys())[0]
        return state
    
    # Firewood-splitting logic: find highest uncertainty or probability branch to deepen
    # For now, just pick the next 'open' branch at current depth or deeper
    # In a more advanced version, this would be a DFS traversal
    pass

async def pick_next_branch(state: CampaignState):
    # logic to select next branch for Specialist/BlindSpot
    pass
