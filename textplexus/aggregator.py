from typing import Dict
from textplexus.schemas import CampaignState, ProbabilityHistory
from textplexus.config import Config

async def aggregator_node(state: CampaignState):
    """
    Probability Aggregator: Applies Bayesian-style update and normalizes siblings.
    """
    focus_id = state.current_focus_id
    if not focus_id or focus_id not in state.hypotheses:
        return state
    
    hypothesis = state.hypotheses[focus_id]
    parent_id = hypothesis.parent_id
    
    # Bayesian Update: P(H|E) = P(H) * L(E|H) / [P(H)*L(E|H) + P(~H)*L(E|~H)]
    # Simplified likelihood: L = 1.0 + impact
    
    evidence_for_focus = [e for e in state.evidence if e.hypothesis_id == focus_id]
    
    # We need to map evidence back to impact scores
    # Since evidence is simplified to string, we'll try to find common patterns or assume default
    total_likelihood_ratio = 1.0
    
    for e in evidence_for_focus:
        impact = 0.0
        if "VIOLATION" in e.content:
            impact = -0.8 # Severe penalty for physics violation
        elif "User Input" in e.source:
            impact = 0.2
        elif "BlindSpot" in e.source:
            impact = -0.1 # Blindspots usually introduce doubt
        else:
            impact = 0.05 # Default small positive evidence from specialists
            
        # Bayesian likelihood factor
        total_likelihood_ratio *= (1.0 + impact)

    # Apply update
    prior = hypothesis.probability
    # Posterior proportional to Prior * Likelihood
    posterior = prior * total_likelihood_ratio
    
    # Clamp to avoid 0 or 1
    posterior = max(0.001, min(0.999, posterior))
    hypothesis.probability = posterior
    
    # Sibling Normalization: ensures sum of probabilities at this level (under same parent) is <= 1.0
    siblings = [h for h in state.hypotheses.values() if h.parent_id == parent_id and h.id != "fallback"]
    if siblings:
        total_p = sum(h.probability for h in siblings)
        if total_p > 1.0:
            for h in siblings:
                h.probability /= total_p
                
    state.probability_history.append(ProbabilityHistory(
        hypothesis_id=focus_id,
        probability=hypothesis.probability,
        reasoning=f"Bayesian update with {len(evidence_for_focus)} evidence pieces. Likelihood ratio: {total_likelihood_ratio:.2f}"
    ))
    
    # Prune
    if hypothesis.probability < Config.PRUNE_THRESHOLD:
        hypothesis.status = "pruned"
        
    # Check convergence
    if hypothesis.probability > Config.CONVERGENCE_THRESHOLD:
        state.convergence_score = hypothesis.probability
        
    return state
