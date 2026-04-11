import asyncio
import argparse
import uuid
import sys
from .schemas import CampaignState
from .graph import create_graph
from .config import Config
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def run_campaign(query: str = None, resume_id: str = None):
    if resume_id:
        print(f"Resuming campaign: {resume_id}")
        campaign_id = resume_id
    else:
        campaign_id = str(uuid.uuid4())[:12]
        print(f"Starting new campaign: {campaign_id}")
    
    state = CampaignState(
        campaign_id=campaign_id,
        query=query or "Undefined Research Query"
    )
    
    config = {"configurable": {"thread_id": campaign_id}}
    
    # Use AsyncSqliteSaver as an async context manager
    async with AsyncSqliteSaver.from_conn_string(Config.CHECKPOINT_DB_PATH) as saver:
        graph = create_graph(checkpointer=saver)
        
        current_state = {"state": state}
        try:
            async for output in graph.astream(current_state, config=config):
                for node_name, node_output in output.items():
                    print(f"--- Node '{node_name}' Finished ---")
                    current_state = node_output
                    if current_state["state"].is_finished:
                        break
                if current_state["state"].is_finished:
                    break
        except Exception as e:
            print(f"Graph execution failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Plexus Research Engine")
    parser.add_argument("--campaign", choices=["new", "resume"], required=True)
    parser.add_argument("--query", type=str, help="Research query for new campaign")
    parser.add_argument("--resume", type=str, help="Campaign ID to resume")
    
    args = parser.parse_args()
    
    if args.campaign == "new" and not args.query:
        print("Error: --query is required for a new campaign.")
        sys.exit(1)
        
    if args.campaign == "resume" and not args.resume:
        print("Error: --resume <ID> is required to resume.")
        sys.exit(1)
        
    asyncio.run(run_campaign(query=args.query, resume_id=args.resume))

if __name__ == "__main__":
    main()
