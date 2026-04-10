from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .schemas import CampaignState
from .agents.supervisor import supervisor_node
from .agents.specialist import specialist_node
from .agents.blindspot import blindspot_node
from .agents.physics_verifier import physics_verifier_node
from .agents.interlocutor import interlocutor_node
from .agents.converger import converger_node
from .agents.archivist_node import archivist_node
from .aggregator import aggregator_node
from .config import Config

class GraphState(TypedDict):
    state: CampaignState

def create_graph():
    workflow = StateGraph(GraphState)

    # Define nodes - wrapping them to match GraphState
    async def wrap_supervisor(x): return {"state": await supervisor_node(x["state"])}
    async def wrap_specialist(x): return {"state": await specialist_node(x["state"])}
    async def wrap_blindspot(x): return {"state": await blindspot_node(x["state"])}
    async def wrap_physics(x): return {"state": await physics_verifier_node(x["state"])}
    async def wrap_aggregator(x): return {"state": await aggregator_node(x["state"])}
    async def wrap_interlocutor(x): return {"state": await interlocutor_node(x["state"])}
    async def wrap_archivist(x): return {"state": await archivist_node(x["state"])}
    async def wrap_converger(x): return {"state": await converger_node(x["state"])}

    workflow.add_node("supervisor", wrap_supervisor)
    workflow.add_node("specialist", wrap_specialist)
    workflow.add_node("blindspot", wrap_blindspot)
    workflow.add_node("physics", wrap_physics)
    workflow.add_node("aggregator", wrap_aggregator)
    workflow.add_node("interlocutor", wrap_interlocutor)
    workflow.add_node("archivist", wrap_archivist)
    workflow.add_node("converger", wrap_converger)

    # Build the edges
    workflow.set_entry_point("archivist")
    
    workflow.add_edge("archivist", "supervisor")
    workflow.add_edge("supervisor", "specialist")
    workflow.add_edge("specialist", "blindspot")
    workflow.add_edge("blindspot", "physics")
    workflow.add_edge("physics", "aggregator")
    workflow.add_edge("aggregator", "interlocutor")
    workflow.add_edge("interlocutor", "archivist")
    
    def should_converge(data: GraphState):
        s = data["state"]
        if s.is_finished:
            return "end"
        if s.convergence_score > Config.CONVERGENCE_THRESHOLD:
            return "converger"
        if s.iteration > Config.MAX_DEPTH:
            return "converger"
        return "supervisor"

    workflow.add_conditional_edges(
        "archivist",
        should_converge,
        {
            "converger": "converger",
            "supervisor": "supervisor",
            "end": END
        }
    )
    
    workflow.add_edge("converger", END)

    # Add persistence
    memory = SqliteSaver.from_conn_string(Config.CHECKPOINT_DB_PATH)
    return workflow.compile(checkpointer=memory)
