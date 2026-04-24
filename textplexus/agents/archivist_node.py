from textplexus.archivist import Archivist
from textplexus.schemas import CampaignState

archivist = Archivist()

async def archivist_node(state: CampaignState):
    """
    Archivist Agent: Single source of truth for reading/writing SQLite.
    Logs every hypothesis, evidence, and probability history.
    """
    await archivist.init_db()
    
    # Save campaign if new
    await archivist.save_campaign(state.campaign_id, state.query)
    
    # Sync hypotheses
    for h_id, h in state.hypotheses.items():
        await archivist.save_hypothesis({
            "id": h_id,
            "campaign_id": state.campaign_id,
            "parent_id": h.parent_id,
            "content": h.content,
            "depth": h.depth,
            "probability": h.probability,
            "status": h.status
        })
        
    # Sync evidence
    for e in state.evidence:
        await archivist.save_evidence({
            "id": e.id,
            "hypothesis_id": e.hypothesis_id,
            "source": e.source,
            "content": e.content,
            "timestamp": e.timestamp
        })
        
    # Sync probability history (usually just the last one)
    if state.probability_history:
        last_p = state.probability_history[-1]
        await archivist.log_probability({
            "hypothesis_id": last_p.hypothesis_id,
            "probability": last_p.probability,
            "reasoning": last_p.reasoning,
            "timestamp": last_p.timestamp
        })
        
    return state
