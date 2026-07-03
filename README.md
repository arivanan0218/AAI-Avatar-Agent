# InterviewAI — AI-Powered Interview Avatar Agent

An AI avatar that conducts structured technical interviews with domain knowledge, real-time voice interaction, NLP preprocessing, RAG-based question grounding, few-shot learning, and Chain-of-Thought evaluation.

## AI Techniques Implemented

| Technique | Module | Detail |
|---|---|---|
| **NLP** (preprocessing + embeddings) | `backend/nlp/preprocessor.py` | NLTK tokenisation, stop-word removal, lemmatisation, OpenAI `text-embedding-3-large` (3072-dim) |
| **Transformer / LLM** | `backend/rag/`, `backend/interview/` | GPT-4o-mini for Q generation + evaluation; `text-embedding-3-large` for semantic search |
| **Generative AI (Avatar)** | `backend/agent.py` | Anam AI real-time talking avatar (generative video synthesis) |
| **Few-Shot Learning** | `backend/prompts/templates.py` | Per-domain, per-difficulty in-context examples guide question calibration |
| **Prompt Engineering** | `backend/prompts/templates.py` | Systematic role prompts, RAG-augmented generation prompt, Chain-of-Thought evaluation |
| **RAG** | `backend/rag/knowledge_base.py` | Pinecone vector store of 35+ domain knowledge chunks; semantic retrieval per turn |
| **Chain-of-Thought** | `backend/interview/evaluator.py` | 5-step reasoning before scoring (technical accuracy, completeness, communication) |

## Project Structure

```
avatar-agent-1/
├── backend/                       Python LiveKit agent + AI pipeline
│   ├── agent.py                   Main entry point (real-time agent, HR intro, scoring)
│   ├── nlp/preprocessor.py        NLP preprocessing pipeline + embeddings
│   ├── rag/
│   │   ├── knowledge_base.py      Pinecone ingestion + semantic query
│   │   └── retriever.py           Async retrieval wrapper
│   ├── interview/
│   │   ├── session_manager.py     Interview state machine + report generation
│   │   ├── question_generator.py  Few-shot + RAG question generation
│   │   └── evaluator.py           Chain-of-Thought answer evaluation
│   ├── prompts/templates.py       All prompt templates + few-shot bank
│   ├── data/                      Provided datasets (domain knowledge bases)
│   │   ├── software_engineering.json
│   │   ├── healthcare.json
│   │   └── finance.json
│   ├── notebooks/                 01-04 experiment notebooks (OpenAI, reproducible)
│   ├── generate_evaluation_charts.py   Evaluation + charts, tracked with MLflow
│   ├── seed_pinecone.py           One-time knowledge-base ingestion
│   ├── pyproject.toml
│   └── .env.example
├── frontend/                      Next.js React web UI (welcome, live session, score card)
└── docs/                          Report, presentation deck, video script (see docs/README.md)
```

## Prerequisites

- **Python 3.12+** and **Node.js 18+** (with `pnpm`)
- API keys for the services listed under *Required API Keys* below

## Quick Start

### Backend

```bash
cd backend
cp .env.example .env
# Fill all API keys in .env

pip install -e ".[notebooks]"     # installs runtime + notebook/eval deps (incl. mlflow)

# Download NLTK data (first run only)
python -c "import nltk; [nltk.download(r) for r in ['punkt_tab','stopwords','wordnet','omw-1.4']]"

# Ingest domain knowledge into Pinecone (one-time)
python seed_pinecone.py

# Start the interview agent
python agent.py dev
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
# Fill LIVEKIT_* keys (URL, API key, secret)

pnpm install
pnpm dev
# Open http://localhost:3000
```

## Interview Flow

1. **Domain selection** — candidate picks Software Engineering, Healthcare, or Finance
2. **HR-style intro** — the avatar (Ava) greets, asks the candidate's name, and invites a self-introduction
3. **Adaptive questions** — up to 8 questions, difficulty progresses easy → medium → hard → expert
4. **Per-turn pipeline** — NLP preprocessing → RAG context retrieval → few-shot question generation
5. **Answer evaluation** — Chain-of-Thought scoring (technical accuracy, completeness, communication); weak answers get a targeted follow-up
6. **Final score** — spoken summary **and** an on-screen score card (score, recommendation, dimension breakdown). Click **"End & See Score"** any time to end early and see the result.

## Supported Interview Domains

| Domain | Topics |
|---|---|
| Software Engineering | DS&A, system design, SOLID, distributed systems, concurrency |
| Healthcare | EHR/FHIR, HIPAA, clinical AI, medical NLP, federated learning |
| Finance | Fraud detection, credit risk, algorithmic trading, NLP on financial filings |

## Running the Notebooks

The notebooks use the same OpenAI stack as the app and have markdown explanations for every major step. Install the extras, register the venv as a Jupyter kernel, then run in order:

```bash
cd backend
pip install -e ".[notebooks]"
python -m ipykernel install --user --name interviewai --display-name "InterviewAI (venv)"
jupyter lab      # open a notebook, select the "InterviewAI (venv)" kernel, run 01 → 04
```

| Notebook | Technique Demonstrated |
|---|---|
| `01_nlp_preprocessing_pipeline.ipynb` | NLP pipeline, embeddings, cosine similarity |
| `02_rag_knowledge_retrieval.ipynb` | RAG retrieval, relevance analysis |
| `03_prompt_engineering.ipynb` | Systematic prompts, few-shot, CoT ablation |
| `04_evaluation_metrics.ipynb` | Scoring analysis, ROUGE-L, session visualisation |

All notebooks require the API keys in `backend/.env`.

## Evaluation & Experiment Tracking (MLflow)

Evaluation is reproducible and tracked with **MLflow**:

```bash
cd backend
python generate_evaluation_charts.py     # CoT + baseline eval → charts in results/, logged to MLflow

# Browse tracked runs (PowerShell):
$env:MLFLOW_ALLOW_FILE_STORE="true"; mlflow ui --backend-store-uri ./mlruns   # http://localhost:5000
```

Outputs: `backend/results/*.png` (charts), `backend/results/evaluation_metrics.json` (raw metrics), and an MLflow run logging params, metrics, and chart artifacts.

## Required API Keys

| Service | Purpose |
|---|---|
| OpenAI | GPT-4o-mini (LLM) + text-embedding-3-large (embeddings) |
| Deepgram | Speech-to-text (STT) |
| Cartesia | Text-to-speech (TTS) |
| LiveKit | Real-time audio/video transport |
| Pinecone | Vector store (RAG) |
| Anam AI | Talking avatar synthesis (optional — graceful voice-only fallback) |
