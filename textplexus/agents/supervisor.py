import uuid
import asyncio
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from textplexus.schemas import CampaignState, Hypothesis, Decomposition
from textplexus.config import Config

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
    
    # Firewood-splitting logic: find an 'open' branch to deepen
    open_branches = [h for h in state.hypotheses.values() if h.status == "open"]
    
    if not open_branches:
        # If no branches are 'open', we might need to backtrack or finish
        print("Supervisor: No open branches to explore. Attempting to converge.")
        state.is_finished = True # Placeholder for ending if nothing else to do
        return state
        
    # Pick the one with highest probability or just the first one for now
    target = sorted(open_branches, key=lambda x: x.probability, reverse=True)[0]
    
    print(f"Supervisor: Deepening branch '{target.content}' (ID: {target.id})")
    
    prompt = f"""You are the Plexus Supervisor. Deepen the following hypothesis branch by decomposing it into {Config.BRANCH_COUNT} more specific sub-hypotheses.
    Parent Research Query: {state.query}
    Current Branch: {target.content}
    
    Provide structured JSON output with 'hypotheses' (list of strings) and 'reasoning'.
    """
    
    response = await llm.with_structured_output(Decomposition).ainvoke(prompt)
    
    if response:
        target.status = "exploring"
        new_hypotheses = {}
        for h_content in response.hypotheses:
            h_id = str(uuid.uuid4())[:8]
            new_hypotheses[h_id] = Hypothesis(
                id=h_id,
                parent_id=target.id,
                content=h_content,
                depth=target.depth + 1,
                probability=target.probability / len(response.hypotheses)
            )
            target.children_ids.append(h_id)
            
        state.hypotheses.update(new_hypotheses)
        state.iteration += 1
        state.current_focus_id = list(new_hypotheses.keys())[0]
        
    return state

async def pick_next_branch(state: CampaignState):
    # This is called by the graph to set the focus for Specialist fleet
    # Current implementation in supervisor_node already sets current_focus_id
    pass
