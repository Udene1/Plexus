import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    DB_PATH = os.getenv("DB_PATH", "plexus_archive.sqlite")
    CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "plexus_checkpoints.sqlite")
    
    # LLM config
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-pro")
    
    # Campaign thresholds
    CONVERGENCE_THRESHOLD = float(os.getenv("CONVERGENCE_THRESHOLD", "0.7"))
    PRUNE_THRESHOLD = float(os.getenv("PRUNE_THRESHOLD", "0.05"))
    MAX_DEPTH = int(os.getenv("MAX_DEPTH", "5"))
    BRANCH_COUNT = int(os.getenv("BRANCH_COUNT", "4"))
