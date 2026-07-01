# Interview Avatar — Backend

Python LiveKit agent that conducts structured AI-powered technical interviews using NLP, RAG, and Chain-of-Thought evaluation.

## AI Techniques Implemented

| Technique | Where | Detail |
|---|---|---|
| NLP preprocessing | `nlp/preprocessor.py` | NLTK tokenisation, stop-word removal, lemmatisation, keyword extraction |
| Transformer embeddings | `nlp/preprocessor.py`, `rag/knowledge_base.py` | OpenAI `text-embedding-3-large` (3072-dim) |
| RAG | `rag/` | Pinecone vector index + semantic retrieval for question grounding |
| Few-shot learning | `prompts/templates.py`, `interview/question_generator.py` | Per-domain, per-difficulty in-context examples |
| Chain-of-Thought | `prompts/templates.py`, `interview/evaluator.py` | 5-step reasoning before scoring (3 dimensions) |
| Systematic prompts | `prompts/templates.py` | Role-anchored system prompt + structured generation prompts |
| Generative AI (Avatar) | `agent.py` | Anam AI real-time avatar synthesis |

## Directory Structure

```
backend/
├── agent.py                   Main LiveKit agent entry point
├── nlp/
│   └── preprocessor.py        NLP pipeline (clean → tokenise → lemmatise → embed)
├── rag/
│   ├── knowledge_base.py      Pinecone ingestion + semantic query
│   └── retriever.py           Async wrapper for the agent
├── interview/
│   ├── session_manager.py     State machine (questions, answers, scores, report)
│   ├── question_generator.py  Few-shot + RAG question generation
│   └── evaluator.py           CoT answer evaluation
├── prompts/
│   └── templates.py           All prompt templates + few-shot example bank
├── data/
│   ├── software_engineering.json
│   ├── healthcare.json
│   └── finance.json
├── notebooks/
│   ├── 01_nlp_preprocessing_pipeline.ipynb
│   ├── 02_rag_knowledge_retrieval.ipynb
│   ├── 03_prompt_engineering.ipynb
│   └── 04_evaluation_metrics.ipynb
├── results/                   Generated charts from notebooks
├── pyproject.toml
└── .env.example
```

## Setup

```bash
# 1. Copy environment variables
cp .env.example .env
# Fill in all API keys in .env

# 2. Install dependencies (requires Python 3.12+)
pip install -e ".[notebooks]"

# 3. Download NLTK data (first run only)
python -c "import nltk; [nltk.download(r) for r in ['punkt_tab','stopwords','wordnet','omw-1.4']]"

# 4. Ingest domain knowledge into Pinecone (run once)
python -c "
from rag.knowledge_base import KnowledgeBase
kb = KnowledgeBase()
for domain in ['software_engineering', 'healthcare', 'finance']:
    n = kb.load_domain(domain)
    print(f'Loaded {n} vectors for {domain}')
"

# 5. Start the agent
python agent.py dev
```

## Supported Interview Domains

Set via room metadata: `{"domain": "software_engineering"}`

- `software_engineering` — DS&A, system design, SOLID, distributed systems
- `healthcare` — EHR, HIPAA, clinical AI, federated learning
- `finance` — risk, fraud detection, credit scoring, algorithmic trading

## Running Notebooks

```bash
cd notebooks
jupyter lab
```

Run in order: 01 → 02 → 03 → 04.
Notebooks 02–04 require API keys in `backend/.env`.
