"""
Generate evaluation-metric charts for the AI Interview Avatar (report Section 6/7).

Runs the project's REAL Chain-of-Thought evaluator (OpenAI gpt-4o-mini) on a mock
interview dataset, plus a non-reasoning "direct scoring" baseline for the CoT-vs-direct
ablation, then renders publication-quality, colour-blind-safe charts to backend/results/.

Usage:
    python generate_evaluation_charts.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import numpy as np
import matplotlib.pyplot as plt
from openai import OpenAI

from interview.evaluator import AnswerEvaluator

# Use the simple local file store (MLflow 3.x requires opting in). This keeps all runs
# in ./mlruns, viewable with `mlflow ui` — no database or server needed.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

try:
    import mlflow
    _MLFLOW = True
except ImportError:  # MLflow is optional — the script still runs without it
    _MLFLOW = False

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# --- Colour-blind-safe palette (Okabe–Ito). Colour follows the ENTITY (answer class),
#     never the method — so it stays consistent across every chart. ------------------
C_STRONG = "#0072B2"  # blue
C_WEAK = "#E69F00"    # amber
C_CUM = "#D55E00"     # vermillion (cumulative-avg line)
C_THRESH = "#6B7280"  # gray (threshold rule)
INK = "#111827"
MUTED = "#6B7280"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.alpha": 0.22,
    "grid.linewidth": 0.8,
    "axes.edgecolor": "#D1D5DB",
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.dpi": 150,
})

# ---------------------------------------------------------------------------
# Mock dataset (identical to notebook 04 for consistency)
# ---------------------------------------------------------------------------
MOCK_QA = [
    {"q_num": 1, "difficulty": "easy",
     "question": "What is the difference between a stack and a queue?",
     "strong": "A stack is LIFO — last in, first out. Used for call stacks and DFS. A queue is FIFO — first in, first out. Used for BFS and task scheduling. Both can be implemented with arrays or linked lists.",
     "weak": "Stack is like plates, queue is like a line. I think stack goes backwards."},
    {"q_num": 2, "difficulty": "easy",
     "question": "What does Big-O notation measure?",
     "strong": "Big-O describes the worst-case growth rate of an algorithm as input size grows. O(1) is constant, O(log n) is binary search, O(n) is linear, O(n log n) is merge sort, O(n^2) is nested loops.",
     "weak": "It measures how fast the program runs, like the speed."},
    {"q_num": 3, "difficulty": "medium",
     "question": "Explain the Single Responsibility Principle.",
     "strong": "SRP states a class should have one and only one reason to change. Each class does one thing — separating data access, business logic, and presentation into distinct layers. It improves maintainability and testability.",
     "weak": "It means the class should be responsible for one thing but I am not sure what that means exactly."},
    {"q_num": 4, "difficulty": "medium",
     "question": "How would you design a caching strategy for a REST API?",
     "strong": "I would use cache-aside with Redis. The app checks Redis first; on miss it queries the DB and populates the cache. TTL based on data freshness. For writes I would use cache invalidation rather than write-through to avoid stale data. Popular endpoints get longer TTLs.",
     "weak": "You can use a cache to store things so it is faster. Like storing in memory."},
    {"q_num": 5, "difficulty": "medium",
     "question": "What is the difference between SQL and NoSQL databases?",
     "strong": "SQL is relational, ACID compliant, with fixed schema — good for complex queries and transactions. NoSQL trades ACID for horizontal scalability and schema flexibility. MongoDB is document-based, Cassandra is wide-column for write-heavy workloads, Redis for caching. Choice depends on consistency needs.",
     "weak": "SQL uses tables and NoSQL doesn't. NoSQL is newer and faster maybe."},
    {"q_num": 6, "difficulty": "hard",
     "question": "Explain the CAP theorem with an example.",
     "strong": "CAP says a distributed system can guarantee at most two of: Consistency, Availability, Partition Tolerance. Since partitions happen, you choose CP or AP. Cassandra is AP — always available but may return stale data. ZooKeeper is CP — consistent but may reject requests during a partition.",
     "weak": "CAP is about databases. Consistency means all data is the same. I think availability means it works."},
    {"q_num": 7, "difficulty": "hard",
     "question": "How do you handle race conditions in a distributed system?",
     "strong": "Use optimistic concurrency with version numbers — check-and-set before writing. For critical sections use distributed locks via Redis SETNX with TTL. Idempotent operations prevent duplicate processing. Event sourcing avoids shared mutable state entirely.",
     "weak": "Use locks. If two things happen at the same time just lock one."},
    {"q_num": 8, "difficulty": "expert",
     "question": "Design a URL shortener at scale handling 100M redirects per day.",
     "strong": "Base62-encode an auto-incremented ID for short codes. Store mappings in a key-value store (DynamoDB for durability, Redis for hot-path caching). Redirect with HTTP 302. CDN caches popular URLs globally. Analytics via async Kafka events. Rate limit writes to prevent abuse.",
     "weak": "Store the long URL with a short key in a database. When someone visits the short URL, look it up and redirect."},
]

DOMAIN = "software_engineering"
THRESHOLD = 6.5  # recommendation threshold

client = OpenAI()
evaluator = AnswerEvaluator()  # real CoT evaluator (OpenAI)

# ---------------------------------------------------------------------------
# Scoring: CoT (our system) vs. Direct (baseline, no reasoning)
# ---------------------------------------------------------------------------
_DIRECT_PROMPT = (
    "Score this {domain} interview answer from 0-10 on three dimensions. "
    'Return ONLY JSON: {{"technical_accuracy": int, "completeness": int, '
    '"communication": int}}. Do not explain.\n\nQuestion: {q}\nAnswer: {a}'
)


def _weighted(d: dict) -> float:
    return round(
        d.get("technical_accuracy", 5) * 0.5
        + d.get("completeness", 5) * 0.3
        + d.get("communication", 5) * 0.2,
        2,
    )


def direct_score(question: str, answer: str) -> float:
    """Baseline: ask for the three scores directly, with no chain-of-thought."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user",
                   "content": _DIRECT_PROMPT.format(domain="software engineering", q=question, a=answer)}],
        temperature=0.1,
        max_tokens=80,
        response_format={"type": "json_object"},
    )
    return _weighted(json.loads(resp.choices[0].message.content))


async def cot_score(question: str, answer: str) -> float:
    """Our system's Chain-of-Thought evaluator."""
    ev = await evaluator.evaluate(question=question, answer=answer, domain=DOMAIN)
    return ev["overall_score"]


def embed(text: str) -> np.ndarray:
    r = client.embeddings.create(model="text-embedding-3-large", input=text)
    return np.array(r.data[0].embedding)


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _label_bars(ax, bars, fmt="%.1f"):
    ax.bar_label(bars, fmt=fmt, padding=2, fontsize=8, color=INK)


# ---------------------------------------------------------------------------
# Run evaluation
# ---------------------------------------------------------------------------
async def run() -> dict:
    print("Scoring answers (CoT + direct baseline) — this makes OpenAI calls...")
    rows = []
    for qa in MOCK_QA:
        s_cot = await cot_score(qa["question"], qa["strong"])
        w_cot = await cot_score(qa["question"], qa["weak"])
        s_dir = direct_score(qa["question"], qa["strong"])
        w_dir = direct_score(qa["question"], qa["weak"])
        rows.append({"q": qa["q_num"], "difficulty": qa["difficulty"],
                     "s_cot": s_cot, "w_cot": w_cot, "s_dir": s_dir, "w_dir": w_dir})
        print(f"  Q{qa['q_num']} ({qa['difficulty']:>6}): "
              f"CoT strong={s_cot:.1f} weak={w_cot:.1f} | direct strong={s_dir:.1f} weak={w_dir:.1f}")

    # Semantic similarity (strong/weak vs question)
    print("Computing semantic similarity (embeddings)...")
    sims = []
    for qa in MOCK_QA:
        qe = embed(qa["question"])
        sims.append({"q": qa["q_num"],
                     "strong": cos(embed(qa["strong"]), qe),
                     "weak": cos(embed(qa["weak"]), qe)})
    return {"rows": rows, "sims": sims}


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def chart_discrimination(rows):
    q = [r["q"] for r in rows]
    s = [r["s_cot"] for r in rows]
    w = [r["w_cot"] for r in rows]
    x = np.arange(len(q))
    fig, ax = plt.subplots(figsize=(10, 5.2))
    b1 = ax.bar(x - 0.2, s, 0.38, label="Strong answer", color=C_STRONG)
    b2 = ax.bar(x + 0.2, w, 0.38, label="Weak answer", color=C_WEAK)
    _label_bars(ax, b1); _label_bars(ax, b2)
    ax.axhline(THRESHOLD, color=C_THRESH, ls="--", lw=1.2)
    ax.text(len(q) - 0.5, THRESHOLD + 0.15, "Recommend ≥ 6.5", color=C_THRESH, fontsize=9, ha="right")
    ax.set_xticks(x, [f"Q{i}" for i in q])
    ax.set_ylim(0, 10.6)
    ax.set_ylabel("Overall score (0–10)")
    ax.set_title("CoT scoring discriminates strong vs. weak answers", fontweight="bold")
    ax.legend(frameon=False, loc="upper right", ncols=2)
    fig.tight_layout()
    p = RESULTS_DIR / "fig_score_discrimination.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


def chart_cot_vs_direct(rows):
    s_cot = np.mean([r["s_cot"] for r in rows]); w_cot = np.mean([r["w_cot"] for r in rows])
    s_dir = np.mean([r["s_dir"] for r in rows]); w_dir = np.mean([r["w_dir"] for r in rows])
    gap_cot, gap_dir = s_cot - w_cot, s_dir - w_dir
    x = np.arange(2)
    fig, ax = plt.subplots(figsize=(8, 5.2))
    b1 = ax.bar(x - 0.2, [s_cot, s_dir], 0.38, label="Strong answer", color=C_STRONG)
    b2 = ax.bar(x + 0.2, [w_cot, w_dir], 0.38, label="Weak answer", color=C_WEAK)
    _label_bars(ax, b1); _label_bars(ax, b2)
    ax.set_xticks(x, [f"Chain-of-Thought\n(gap {gap_cot:.1f})", f"Direct scoring\n(gap {gap_dir:.1f})"])
    ax.set_ylim(0, 10.6)
    ax.set_ylabel("Mean overall score (0–10)")
    ax.set_title("Ablation: CoT and direct scoring both separate answer quality", fontweight="bold")
    ax.legend(frameon=False, loc="upper right", ncols=2)
    fig.tight_layout()
    p = RESULTS_DIR / "fig_cot_vs_direct.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p, gap_cot, gap_dir


def chart_progression(rows):
    # Mid-level candidate: strong on easy/medium, weak on hard/expert
    scores = [r["s_cot"] if r["difficulty"] in ("easy", "medium") else r["w_cot"] for r in rows]
    cum = [float(np.mean(scores[: i + 1])) for i in range(len(scores))]
    xs = [r["q"] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.plot(xs, scores, "o-", color=C_STRONG, lw=2.2, ms=8, label="Question score")
    ax.plot(xs, cum, "s--", color=C_CUM, lw=1.8, ms=6, label="Cumulative average")
    ax.axhline(THRESHOLD, color=C_THRESH, ls=":", lw=1.2)
    ax.text(xs[0], THRESHOLD + 0.15, "Recommend ≥ 6.5", color=C_THRESH, fontsize=9)
    for r, sc in zip(rows, scores):
        ax.annotate(r["difficulty"], (r["q"], sc), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=8, color=MUTED)
    ax.set_xticks(xs, [f"Q{i}" for i in xs])
    ax.set_ylim(0, 10.6)
    ax.set_ylabel("Score (0–10)")
    ax.set_title("Mid-level candidate: score progression across the interview", fontweight="bold")
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    p = RESULTS_DIR / "fig_score_progression.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


def chart_by_difficulty(rows):
    order = ["easy", "medium", "hard", "expert"]
    s = [np.mean([r["s_cot"] for r in rows if r["difficulty"] == d]) for d in order]
    w = [np.mean([r["w_cot"] for r in rows if r["difficulty"] == d]) for d in order]
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    b1 = ax.bar(x - 0.2, s, 0.38, label="Strong answer", color=C_STRONG)
    b2 = ax.bar(x + 0.2, w, 0.38, label="Weak answer", color=C_WEAK)
    _label_bars(ax, b1); _label_bars(ax, b2)
    ax.set_xticks(x, [d.title() for d in order])
    ax.set_ylim(0, 10.6)
    ax.set_ylabel("Mean overall score (0–10)")
    ax.set_title("Average scores by difficulty level", fontweight="bold")
    ax.legend(frameon=False, loc="upper right", ncols=2)
    fig.tight_layout()
    p = RESULTS_DIR / "fig_scores_by_difficulty.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p


def chart_similarity(sims):
    s = np.mean([r["strong"] for r in sims]); w = np.mean([r["weak"] for r in sims])
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    bars = ax.bar(["Strong", "Weak"], [s, w], 0.5, color=[C_STRONG, C_WEAK])
    ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=9, color=INK)
    ax.set_ylim(0, max(s, w) * 1.25)
    ax.set_ylabel("Mean cosine similarity to question")
    ax.set_title("Strong answers align more with the question", fontweight="bold")
    fig.tight_layout()
    p = RESULTS_DIR / "fig_semantic_similarity.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p, s, w


PARAMS = {
    "llm_model": "gpt-4o-mini",
    "embedding_model": "text-embedding-3-large",
    "temperature": 0.1,
    "num_questions": len(MOCK_QA),
    "weight_technical_accuracy": 0.5,
    "weight_completeness": 0.3,
    "weight_communication": 0.2,
    "recommend_threshold": THRESHOLD,
    "scoring_methods": "chain_of_thought,direct",
    "domain": DOMAIN,
}


def _evaluate_and_plot():
    """Run the evaluation, render charts, and return (rows, sims, paths, metrics)."""
    data = asyncio.run(run())
    rows, sims = data["rows"], data["sims"]

    paths = [chart_discrimination(rows)]
    p_ablation, gap_cot, gap_dir = chart_cot_vs_direct(rows)
    paths.append(p_ablation)
    paths.append(chart_progression(rows))
    paths.append(chart_by_difficulty(rows))
    p_sim, sim_s, sim_w = chart_similarity(sims)
    paths.append(p_sim)

    metrics = {
        "mean_strong_cot": float(np.mean([r["s_cot"] for r in rows])),
        "mean_weak_cot": float(np.mean([r["w_cot"] for r in rows])),
        "mean_strong_direct": float(np.mean([r["s_dir"] for r in rows])),
        "mean_weak_direct": float(np.mean([r["w_dir"] for r in rows])),
        "gap_cot": float(gap_cot),
        "gap_direct": float(gap_dir),
        "cot_improvement_over_direct": float(gap_cot - gap_dir),
        "cosine_strong_to_question": float(sim_s),
        "cosine_weak_to_question": float(sim_w),
    }
    return rows, sims, paths, metrics


def _print_headline(m):
    print("\n================ HEADLINE METRICS (paste into report) ================")
    print(f"Mean strong score (CoT):        {m['mean_strong_cot']:.2f} / 10")
    print(f"Mean weak score   (CoT):        {m['mean_weak_cot']:.2f} / 10")
    print(f"Discrimination gap  — CoT:      {m['gap_cot']:.2f}")
    print(f"Discrimination gap  — Direct:   {m['gap_direct']:.2f}")
    print(f"CoT improvement over direct:    {m['cot_improvement_over_direct']:+.2f} points")
    print(f"Cosine sim to question (strong):{m['cosine_strong_to_question']:.3f}")
    print(f"Cosine sim to question (weak):  {m['cosine_weak_to_question']:.3f}")


def main():
    if not _MLFLOW:
        print("MLflow not installed — running without experiment tracking "
              "(pip install mlflow to enable).")
        rows, sims, paths, metrics = _evaluate_and_plot()
        _print_headline(metrics)
        _save_raw(rows, sims, metrics)
        print("\nCharts saved to backend/results/:")
        for p in paths:
            print(f"  - {p.name}")
        return

    # --- MLflow experiment tracking (local file store, no server needed) ---
    mlflow.set_tracking_uri((Path(__file__).parent / "mlruns").as_uri())
    mlflow.set_experiment("InterviewAI-Evaluation")

    with mlflow.start_run(run_name="cot-vs-direct-scoring") as run:
        mlflow.set_tags({
            "project": "InterviewAI",
            "stage": "evaluation",
            "component": "answer-scorer",
        })
        mlflow.log_params(PARAMS)

        rows, sims, paths, metrics = _evaluate_and_plot()

        mlflow.log_metrics(metrics)
        # per-question scores as a stepped metric series
        for r in rows:
            mlflow.log_metric("strong_cot_by_question", r["s_cot"], step=r["q"])
            mlflow.log_metric("weak_cot_by_question", r["w_cot"], step=r["q"])

        # log charts + raw data as run artifacts
        for p in paths:
            mlflow.log_artifact(str(p), artifact_path="charts")
        raw_path = _save_raw(rows, sims, metrics)
        mlflow.log_artifact(str(raw_path), artifact_path="data")

        _print_headline(metrics)
        print("\nCharts saved to backend/results/ and logged to MLflow run:")
        for p in paths:
            print(f"  - {p.name}")
        print(f"\nMLflow run id: {run.info.run_id}")
        print("View the experiment UI (PowerShell):")
        print('  $env:MLFLOW_ALLOW_FILE_STORE="true"; mlflow ui --backend-store-uri ./mlruns')


def _save_raw(rows, sims, metrics) -> Path:
    """Persist the raw per-question results + summary metrics as JSON."""
    out = RESULTS_DIR / "evaluation_metrics.json"
    out.write_text(json.dumps(
        {"params": PARAMS, "summary": metrics, "per_question": rows, "similarity": sims},
        indent=2,
    ), encoding="utf-8")
    return out


if __name__ == "__main__":
    main()
