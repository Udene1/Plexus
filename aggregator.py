from typing import Dict
from .schemas import CampaignState, ProbabilityHistory
from .config import Config

async def aggregator_node(state: CampaignState):
    """
    Probability Aggregator: Applies Bayesian-style update after physics filter and prunes branches.
    """
    focus_id = state.current_focus_id
    if not focus_id:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    
    # Simple weighted aggregation for v0.1
    # We look for evidence for this hypothesis
    evidence_for_focus = [e for e in state.evidence if e.hypothesis_id == focus_id]
    
    # In a real Bayesian update, we'd have likelihoods. 
    # Here we use a simplified version: P(H|E) = P(H) * (1 + sum(impact))
    # This is not strictly Bayesian but follows the 'weighted ensemble' requirement.
    
    # Note: impact logic is currently simplified.
    # We'll assume LLM specialists give a score, and physics violations give a hard penalty.
    
    total_impact = 0.0
    for e in evidence_for_focus:
        if "VIOLATION" in e.content:
            total_impact -= 0.5 # Heavy penalty
        elif e.source == "User Input":
            total_impact += 0.1 # Small boost for user confirmation
        else:
            # For specialist/blindspot, we'd ideally have the impact score in the evidence object
            # For now, let's assume a default small impact if not specified
            total_impact += 0.05
            
    new_prob = hypothesis.probability * (1.0 + total_impact)
    new_prob = max(0.01, min(0.99, new_prob))
    
    hypothesis.probability = new_prob
    
    # Normalize probabilities among siblings if needed
    # (Skipping sibling normalization for now to keep it simple, 
    # but in DFS/BFS this would be handled at the branch level)
    
    state.probability_history.append(ProbabilityHistory(
        hypothesis_id=focus_id,
        probability=new_prob,
        reasoning=f"Aggregated {len(evidence_for_focus)} pieces of evidence."
    ))
    
    # Prune
    if new_prob < Config.PRUNE_THRESHOLD:
        hypothesis.status = "pruned"
        
    # Check convergence
    if new_prob > Config.CONVERGENCE_THRESHOLD:
        state.convergence_score = new_prob
        
    return state
