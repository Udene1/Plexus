import uuid
from ..schemas import CampaignState, Evidence

async def interlocutor_node(state: CampaignState):
    """
    Interlocutor Agent: Pauses the graph, shows insights, and asks for user input.
    """
    print("\n" + "="*50)
    print("PLEXUS INTERLOCUTOR - INSIGHTS WAVE COMPLETE")
    print(f"Current Focus: {state.hypotheses[state.current_focus_id].content}")
    print(f"Current Probability: {state.hypotheses[state.current_focus_id].probability:.2f}")
    
    recent_evidence = [e for e in state.evidence if e.hypothesis_id == state.current_focus_id][-3:]
    print("\nRecent Evidence:")
    for e in recent_evidence:
        print(f"- [{e.source}] {e.content[:100]}...")
        
    user_input = input("\nEnter your feedback or new evidence (or press Enter to continue): ").strip()
    
    if user_input:
        e_id = str(uuid.uuid4())[:8]
        evidence = Evidence(
            id=e_id,
            hypothesis_id=state.current_focus_id,
            source="User Input",
            content=user_input
        )
        state.evidence.append(evidence)
        print("User feedback injected.")
        
    print("="*50 + "\n")
    return state
