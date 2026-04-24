# Plexus

Plexus is a production-ready, open-source persistent multi-agent research and prediction engine.

## Core Purpose
Plexus takes any complex problem and systematically narrows it down to the single tightest “last line” most-likely outcome while holding every fact, hypothesis, evidence, and probability perfectly linked.

## Architecture
- **Supervisor**: Decomposes questions into hypothesis branches.
- **Specialist Fleet**: Parallel agents attacking from divergent angles.
- **BlindSpot Agent**: Surfaces overlooked risks and scenarios.
- **Physics Verifier**: Hard truth filter using first-principles constraints.
- **Interlocutor**: Human-in-the-loop interaction.
- **Archivist**: SQLite-backed persistence for the hypothesis tree and evidence.

## Getting Started

### Installation
```bash
pip install -r requirements.txt
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
