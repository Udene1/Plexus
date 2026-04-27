"""
Supervisor Agent — Iterative Feedback-Driven Hypothesis Decomposition.

Strategy: Start with N high-level "logs", let agents research them,
then use the evidence + blindspot findings to decide where to split deeper.
Repeats until branches converge or are pruned.
"""
import uuid
import asyncio
from typing import List
from textplexus.schemas import CampaignState, Hypothesis, Decomposition
from textplexus.config import Config, get_llm

llm = get_llm()


async def supervisor_node(state: CampaignState):
    """
    Supervisor Agent: Decomposes query into hypothesis branches
    and iteratively deepens them based on evidence feedback.
    """

    # ── Phase 1: Initial Decomposition (first call only) ─────────────
    if not state.hypotheses:
        prompt = f"""You are the Plexus Supervisor. Decompose the following research query into {Config.BRANCH_COUNT} top-level, mutually exclusive hypothesis branches.
Query: {state.query}

Provide structured JSON output with 'hypotheses' (list of strings) and 'reasoning'.
"""
        response = await _invoke_with_retries(prompt)

        if not response:
            h_id = "fallback"
            state.hypotheses[h_id] = Hypothesis(
                id=h_id, content="General research on " + state.query,
                depth=0, probability=1.0
            )
            state.current_focus_id = h_id
            return state

        new_hypotheses = {}
        for h_content in response.hypotheses:
            h_id = str(uuid.uuid4())[:8]
            new_hypotheses[h_id] = Hypothesis(
                id=h_id, content=h_content, depth=0,
                probability=1.0 / len(response.hypotheses),
            )

        state.hypotheses.update(new_hypotheses)
        state.iteration += 1
        state.current_focus_id = list(new_hypotheses.keys())[0]
        return state

    # ── Phase 2: Evidence-Informed Deepening ─────────────────────────
    # Gather intelligence from previous cycle
    evidence_summary = _build_evidence_summary(state)
    blindspot_findings = _get_blindspot_findings(state)

    # Find branches eligible for deepening:
    #   - "open" status (not yet explored, pruned, or converged)
    #   - Within max depth
    open_branches = [
        h for h in state.hypotheses.values()
        if h.status == "open" and h.depth < Config.MAX_DEPTH
    ]

    if not open_branches:
        # All branches explored / pruned / converged — campaign is done
        print("Supervisor: No open branches left. Finishing campaign.")
        state.is_finished = True
        return state

    # Rank branches: prioritize by probability (most promising first),
    # but also boost branches flagged by blindspot analysis
    for h in open_branches:
        blindspot_boost = h.metadata.get("blindspot_priority", 0.0)
        h.metadata["_sort_score"] = h.probability + blindspot_boost

    target = max(open_branches, key=lambda h: h.metadata.get("_sort_score", 0))

    # Clean up temp sort score
    for h in open_branches:
        h.metadata.pop("_sort_score", None)

    print(f"Supervisor: Deepening branch '{target.content[:60]}...' (depth={target.depth}, p={target.probability:.3f})")

    # Ask the LLM to decompose, informed by what we've learned
    prompt = f"""You are the Plexus Supervisor. Based on the evidence gathered so far, decompose the following hypothesis into {Config.BRANCH_COUNT} more specific sub-hypotheses.

Parent Research Query: {state.query}
Current Branch: {target.content}

Evidence gathered so far:
{evidence_summary}

Blindspot findings (overlooked factors):
{blindspot_findings}

Use the evidence and blindspot findings to make INFORMED sub-hypotheses.
Focus on the areas where the evidence is weakest or most contested.
Provide structured JSON output with 'hypotheses' (list of strings) and 'reasoning'.
"""
    response = await _invoke_with_retries(prompt)

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
                probability=target.probability / len(response.hypotheses),
            )
            target.children_ids.append(h_id)

        state.hypotheses.update(new_hypotheses)
        state.iteration += 1
        # Focus the next cycle on the first new sub-hypothesis
        state.current_focus_id = list(new_hypotheses.keys())[0]

    return state


# ── Helpers ──────────────────────────────────────────────────────────

def _build_evidence_summary(state: CampaignState) -> str:
    """Summarize the most recent evidence for the supervisor's context."""
    if not state.evidence:
        return "No evidence gathered yet."

    # Group by hypothesis and take the 3 most recent per branch
    from collections import defaultdict
    by_hyp = defaultdict(list)
    for e in state.evidence:
        by_hyp[e.hypothesis_id].append(e)

    lines = []
    for h_id, evidences in by_hyp.items():
        hyp = state.hypotheses.get(h_id)
        if not hyp:
            continue
        label = hyp.content[:80]
        lines.append(f"Branch '{label}' (p={hyp.probability:.3f}):")
        for e in evidences[-3:]:  # most recent 3
            lines.append(f"  [{e.source}] {e.content[:120]}")
    return "\n".join(lines) if lines else "No evidence gathered yet."


def _get_blindspot_findings(state: CampaignState) -> str:
    """Extract blindspot-specific evidence for the supervisor."""
    blindspots = [e for e in state.evidence if "BlindSpot" in e.source]
    if not blindspots:
        return "No blindspots identified yet."

    lines = []
    for b in blindspots[-5:]:  # last 5 blindspot findings
        hyp = state.hypotheses.get(b.hypothesis_id)
        label = hyp.content[:60] if hyp else b.hypothesis_id
        lines.append(f"  [{label}] {b.content[:150]}")

        # Boost parent hypothesis priority so supervisor deepens it
        if hyp and hyp.status == "open":
            hyp.metadata["blindspot_priority"] = hyp.metadata.get("blindspot_priority", 0.0) + 0.1

    return "\n".join(lines)


async def _invoke_with_retries(prompt: str, retries: int = 3) -> Decomposition | None:
    """Invoke LLM with structured output and retry on failure."""
    for i in range(retries):
        try:
            response = await llm.with_structured_output(Decomposition).ainvoke(prompt)
            if response:
                return response
        except Exception as e:
            print(f"Supervisor retry {i + 1}/{retries}: {e}")
        await asyncio.sleep(3)

    print("Error: Supervisor failed after retries. Returning None.")
    return None


async def pick_next_branch(state: CampaignState):
    """Called by the graph to cycle focus across open branches."""
    open_branches = [
        h for h in state.hypotheses.values()
        if h.status == "open" and h.depth < Config.MAX_DEPTH
    ]
    if open_branches:
        # Round-robin: pick the branch that has the least evidence
        evidence_counts = {}
        for e in state.evidence:
            evidence_counts[e.hypothesis_id] = evidence_counts.get(e.hypothesis_id, 0) + 1

        least_explored = min(open_branches, key=lambda h: evidence_counts.get(h.id, 0))
        state.current_focus_id = least_explored.id
    return state
