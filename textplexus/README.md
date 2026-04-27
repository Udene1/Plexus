# Plexus

Plexus is a production-ready, open-source persistent multi-agent research and prediction engine. 

## Core Purpose
Plexus takes any complex problem and systematically narrows it down to the single tightest “last line” most-likely outcome while holding every fact, hypothesis, evidence, and probability perfectly linked.

## Architecture & recent upgrades

- **Supervisor (Iterative Decomposition)**: Employs "Firewood Splitting" — starting with high-level branches and iteratively deepening the tree based on evidence and blindspot discovery.
- **Specialist Fleet**: Parallel agents attacking from divergent angles.
- **BlindSpot Agent**: Surfaces overlooked risks and scenarios, modifying branch priorities.
- **Physics Verifier (Sandbox)**: Hard truth filter. Executes Python code in a secure sandbox (`PhysicsSandbox`) utilizing `numpy`, `sympy`, and `scipy.integrate` to test causal constraints, conservation laws, and thermodynamics.
- **Aggregator**: Uses precise metadata violation scoring for deep Bayesian likelihood updates.
- **Interlocutor**: Human-in-the-loop interaction.
- **Archivist**: SQLite-backed persistence for the hypothesis tree and evidence.

## LLM Configuration

Plexus defaults to **DeepSeek** (`deepseek-chat`) as its primary heavy-lifting engine, taking advantage of its strong reasoning capabilities. It falls back to Gemini `gemini-2.5-flash` if DeepSeek keys are unavailable.

1. Ensure you have the `langchain-openai` module installed.
2. Provide your `DEEPSEEK_API_KEY` in the `.env` file to unlock primary features.

## Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Create a `.env` file referencing `.env.template`:
```env
GOOGLE_API_KEY=your_gemini_key
DEEPSEEK_API_KEY=your_deepseek_key
MODEL_NAME=gemini-2.5-flash
DEEPSEEK_MODEL=deepseek-chat
```

### Usage
Run a new research campaign:
```bash
python main.py --campaign new --query "Will ETH outperform BTC in Q3 2026?"
```

Resume an existing campaign:
```bash
python main.py --resume <CAMPAIGN_ID>
```

## License
MIT License
