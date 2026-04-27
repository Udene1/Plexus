import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this config file
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)

class Config:
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DB_PATH = os.getenv("DB_PATH", "plexus_archive.sqlite")
    CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "plexus_checkpoints.sqlite")
    
    # LLM config
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # Campaign thresholds
    CONVERGENCE_THRESHOLD = float(os.getenv("CONVERGENCE_THRESHOLD", "0.7"))
    PRUNE_THRESHOLD = float(os.getenv("PRUNE_THRESHOLD", "0.05"))
    MAX_DEPTH = int(os.getenv("MAX_DEPTH", "5"))
    BRANCH_COUNT = int(os.getenv("BRANCH_COUNT", "4"))

def get_llm(use_fallback=False, temperature=0.7):
    """Factory to get the primary (DeepSeek) or fallback (Gemini) LLM."""
    if not use_fallback and Config.DEEPSEEK_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=Config.DEEPSEEK_MODEL, 
            api_key=Config.DEEPSEEK_API_KEY, 
            base_url="https://api.deepseek.com",
            temperature=temperature
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=Config.MODEL_NAME, 
            google_api_key=Config.GEMINI_API_KEY,
            temperature=temperature
        )

