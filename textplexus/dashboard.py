import streamlit as st
import pandas as pd
import asyncio
import sys
import os

# Add the parent directory to sys.path to allow absolute imports of textplexus
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textplexus.archivist import Archivist, CampaignModel, HypothesisModel, EvidenceModel
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# This dashboard reads from the SQLAlchemy models defined in archivist.py
st.set_page_config(page_title="Plexus Dashboard", layout="wide")

st.title("🌐 Plexus Research Dashboard")
st.sidebar.header("Campaign Settings")

archivist = Archivist()

async def get_campaigns():
    async with archivist.async_session() as session:
        result = await session.execute(select(CampaignModel).order_by(CampaignModel.created_at.desc()))
        return result.scalars().all()

async def get_hypotheses(campaign_id):
    async with archivist.async_session() as session:
        result = await session.execute(
            select(HypothesisModel).where(HypothesisModel.campaign_id == campaign_id)
        )
        return result.scalars().all()

async def get_evidence(campaign_id):
    async with archivist.async_session() as session:
        # Join with hypotheses to get the content
        result = await session.execute(
            select(EvidenceModel, HypothesisModel)
            .join(HypothesisModel, EvidenceModel.hypothesis_id == HypothesisModel.id)
            .where(HypothesisModel.campaign_id == campaign_id)
            .order_by(EvidenceModel.timestamp.desc())
        )
        return result.all()

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Initialize DB once
run_async(archivist.init_db())

campaigns = run_async(get_campaigns())

if not campaigns:
    st.warning("No campaigns found in database.")
else:
    campaign_options = {f"{c.query} ({c.id})": c.id for c in campaigns}
    selected_name = st.sidebar.selectbox("Select Campaign", list(campaign_options.keys()))
    campaign_id = campaign_options[selected_name]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Hypothesis Tree")
        hypotheses = run_async(get_hypotheses(campaign_id))
        if hypotheses:
            data = [{
                "ID": h.id,
                "Content": h.content,
                "Probability": h.probability,
                "Status": h.status,
                "Depth": h.depth
            } for h in hypotheses]
            df_h = pd.DataFrame(data)
            st.dataframe(df_h.style.background_gradient(subset=["Probability"], cmap="Greens"))
            st.bar_chart(df_h.set_index("Content")["Probability"])
        else:
            st.info("No hypotheses found for this campaign.")

    with col2:
        st.subheader("Recent Evidence")
        evidence_pairs = run_async(get_evidence(campaign_id))
        if evidence_pairs:
            for ev, hyp in evidence_pairs[:10]:
                st.markdown(f"**{ev.source}** on *{hyp.content[:30]}...*")
                st.caption(ev.content[:200] + "...")
                st.divider()
        else:
            st.info("No evidence collected yet.")

st.sidebar.divider()
if st.sidebar.button("Refresh Data"):
    st.rerun()
