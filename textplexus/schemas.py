from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Hypothesis(BaseModel):
    id: str
    parent_id: Optional[str] = None
    content: str
    depth: int
    probability: float = 0.0
    status: str = "open"  # open, exploring, converged, pruned
    children_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Evidence(BaseModel):
    id: str
    hypothesis_id: str
    source: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProbabilityHistory(BaseModel):
    hypothesis_id: str
    probability: float
    timestamp: datetime = Field(default_factory=datetime.now)
    reasoning: str

class CampaignState(BaseModel):
    campaign_id: str
    query: str
    hypotheses: Dict[str, Hypothesis] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)
    probability_history: List[ProbabilityHistory] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    convergence_score: float = 0.0
    current_focus_id: Optional[str] = None
    iteration: int = 0
    is_finished: bool = False

# Structured Output Models for Agents
class Decomposition(BaseModel):
    hypotheses: List[str] = Field(description="List of top-level hypothesis branches")
    reasoning: str

class SpecialistOutput(BaseModel):
    evidence: str
    impact_on_probability: float = Field(description="Change in probability score (-1.0 to 1.0)")
    reasoning: str

class PhysicsCheckResult(BaseModel):
    valid: bool
    violated_law: Optional[str] = None
    quantitative_constraint: Optional[str] = None
    suggested_code: Optional[str] = Field(default=None, description="Python code to execute in sandbox for verification")
    suggested_adjustment: Optional[str] = None
    reasoning: str
