import asyncio
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime
from .config import Config

Base = declarative_base()

class CampaignModel(Base):
    __tablename__ = 'campaigns'
    id = Column(String, primary_key=True)
    query = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")

class HypothesisModel(Base):
    __tablename__ = 'hypotheses'
    id = Column(String, primary_key=True)
    campaign_id = Column(String, ForeignKey('campaigns.id'))
    parent_id = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    depth = Column(Integer, default=0)
    probability = Column(Float, default=0.0)
    status = Column(String, default="open")
    
    campaign = relationship("CampaignModel", backref="hypotheses")

class EvidenceModel(Base):
    __tablename__ = 'evidence'
    id = Column(String, primary_key=True)
    hypothesis_id = Column(String, ForeignKey('hypotheses.id'))
    source = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    hypothesis = relationship("HypothesisModel", backref="evidence")

class ProbabilityHistoryModel(Base):
    __tablename__ = 'probability_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hypothesis_id = Column(String, ForeignKey('hypotheses.id'))
    probability = Column(Float)
    reasoning = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Archivist:
    def __init__(self, db_url: str = f"sqlite+aiosqlite:///{Config.DB_PATH}"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save_campaign(self, campaign_id: str, query: str):
        async with self.async_session() as session:
            campaign = CampaignModel(id=campaign_id, query=query)
            await session.merge(campaign)
            await session.commit()

    async def save_hypothesis(self, h_data: dict):
        async with self.async_session() as session:
            hypothesis = HypothesisModel(**h_data)
            await session.merge(hypothesis)
            await session.commit()

    async def save_evidence(self, e_data: dict):
        async with self.async_session() as session:
            evidence = EvidenceModel(**e_data)
            await session.merge(evidence)
            await session.commit()

    async def log_probability(self, p_data: dict):
        async with self.async_session() as session:
            history = ProbabilityHistoryModel(**p_data)
            session.add(history)
            await session.commit()
            
    async def get_campaign_state(self, campaign_id: str):
        # This would reconstruct the state from DB if needed
        # For now, LangGraph checkpoint handles most state reconstruction
        pass
