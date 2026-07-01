"""
Prompt Templates — Systematic prompt engineering for the AI Interview Avatar.

Design strategy:
  - INTERVIEWER_SYSTEM_PROMPT  : role + behavioural constraints
  - QUESTION_GENERATION_PROMPT : few-shot + RAG-context guided generation
  - CHAIN_OF_THOUGHT_EVALUATION_PROMPT : CoT scoring across 3 dimensions
  - FEW_SHOT_EXAMPLES          : in-context learning bank per domain
"""

# ---------------------------------------------------------------------------
# 1. Interviewer System Prompt
# ---------------------------------------------------------------------------
INTERVIEWER_SYSTEM_PROMPT = """You are an expert AI interviewer conducting a structured technical interview for a {domain} role.

Behavioural rules:
- This is a live, two-way conversation — sound like a real human interviewer, not a quiz machine.
- Always REACT to what the candidate actually said before moving on (a brief, specific acknowledgement — not a generic "thanks").
- Ask ONE focused question at a time — never bundle multiple questions.
- When you are given a question to ask, rephrase it in your OWN natural words and, where it fits, connect it to what was just discussed. Never read a question robotically or announce "Question 3".
- When an answer is vague, shallow, or incomplete, ask a natural follow-up to probe deeper before moving on — exactly as a real interviewer would.
- Do NOT reveal whether the answer was correct or incorrect during the interview.
- Keep your spoken turns short and conversational; this is a real-time voice conversation.
- Maintain a warm, professional, encouraging tone throughout.
- If the candidate says they don't know or asks you to repeat, respond kindly and naturally.
- When you deliver the final performance summary, be specific, structured, and constructive.

Your deep {domain} expertise allows you to assess:
  1. Technical accuracy — correctness of facts, terminology, and reasoning.
  2. Completeness — coverage of key concepts expected for the role level.
  3. Communication — clarity, structure, and conciseness of the response.
"""

# ---------------------------------------------------------------------------
# 2. Question Generation Prompt (Few-Shot + RAG)
# ---------------------------------------------------------------------------
QUESTION_GENERATION_PROMPT = """Generate one technical interview question for a {domain} interview.

Constraints:
  - Difficulty  : {difficulty}
  - Question #  : {question_number} of {total_questions}
  - easy   → conceptual / definition questions
  - medium  → application / scenario questions
  - hard    → architectural / trade-off questions
  - expert  → system-design / edge-case questions

Relevant domain knowledge retrieved via RAG (use this to make the question accurate):
{context}

Few-shot examples of high-quality questions at this difficulty level:
{few_shot_examples}

Questions already asked this session (do NOT repeat similar themes):
{previously_asked}

Output ONLY the question text — no preamble, no labels, no explanation.
"""

# ---------------------------------------------------------------------------
# 3. Chain-of-Thought Evaluation Prompt
# ---------------------------------------------------------------------------
CHAIN_OF_THOUGHT_EVALUATION_PROMPT = """Evaluate the candidate answer below using step-by-step chain-of-thought reasoning.
Return a single JSON object — no markdown fences, no extra text.

Domain   : {domain}
Question : {question}
Answer   : {answer}

Reasoning steps (work through each before scoring):
  Step 1 — List the key concepts a strong answer must cover for this {domain} question.
  Step 2 — Identify which of those concepts the candidate actually addressed.
  Step 3 — Check for technical inaccuracies or misconceptions in what was stated.
  Step 4 — Assess whether the explanation was clear and well-structured.
  Step 5 — Assign integer scores (0–10) for each dimension.

Return exactly this JSON schema:
{{
  "reasoning": "<your step-by-step analysis as a single string>",
  "technical_accuracy": <integer 0-10>,
  "completeness": <integer 0-10>,
  "communication": <integer 0-10>,
  "key_concepts_covered": ["<concept>", ...],
  "key_concepts_missing": ["<concept>", ...],
  "feedback": "<2-3 sentence constructive feedback addressed to the candidate>"
}}
"""

# ---------------------------------------------------------------------------
# 4. Final Report Prompt
# ---------------------------------------------------------------------------
FINAL_REPORT_PROMPT = """You are delivering the closing summary of a {domain} technical interview.
Speak naturally (this is voiced), but be structured.

Performance data:
{report_json}

Deliver in this order:
1. Overall verdict ({recommendation}) with the average score ({average_score}/10).
2. Two or three specific strengths observed during the interview.
3. Two or three concrete areas for improvement.
4. An encouraging closing remark.

Keep it under 90 seconds of speech.
"""

# ---------------------------------------------------------------------------
# 5. Few-Shot Example Bank (in-context learning per domain)
# ---------------------------------------------------------------------------
FEW_SHOT_EXAMPLES: dict[str, list[dict]] = {
    "software_engineering": [
        {
            "difficulty": "easy",
            "question": "What is the difference between a stack and a queue?",
            "ideal_hint": "LIFO vs FIFO; typical use-cases (call stack, BFS queue).",
        },
        {
            "difficulty": "easy",
            "question": "What does a version control system like Git give you?",
            "ideal_hint": "Change history, branching, collaboration, rollback.",
        },
        {
            "difficulty": "medium",
            "question": "How would you design a caching layer for a high-traffic REST API?",
            "ideal_hint": "Cache-aside vs write-through, TTL, Redis, invalidation strategy, CDN.",
        },
        {
            "difficulty": "medium",
            "question": "Explain the SOLID principles and give a concrete example of one.",
            "ideal_hint": "SRP, OCP, LSP, ISP, DIP — pick one and illustrate with code.",
        },
        {
            "difficulty": "hard",
            "question": "How do you handle race conditions in a distributed microservices system?",
            "ideal_hint": "Optimistic concurrency, distributed locks (Redis/ZooKeeper), idempotency, saga pattern.",
        },
        {
            "difficulty": "hard",
            "question": "Compare eventual consistency and strong consistency — when would you choose each?",
            "ideal_hint": "CAP theorem, partition tolerance trade-offs, CRDT, use-case examples.",
        },
        {
            "difficulty": "expert",
            "question": "Design a real-time collaborative document editing system that scales to millions of users.",
            "ideal_hint": "OT vs CRDT, WebSocket fan-out, conflict resolution, storage sharding.",
        },
    ],
    "healthcare": [
        {
            "difficulty": "easy",
            "question": "What is the difference between an EHR and an EMR?",
            "ideal_hint": "EHR is interoperable across providers; EMR is practice-specific.",
        },
        {
            "difficulty": "medium",
            "question": "How would you build a symptom checker AI while managing clinical liability?",
            "ideal_hint": "Triage not diagnosis, confidence thresholds, mandatory clinician review, disclaimers.",
        },
        {
            "difficulty": "hard",
            "question": "What are the core challenges of applying ML to medical imaging diagnosis?",
            "ideal_hint": "Class imbalance, annotation quality, interpretability, regulatory approval (FDA 510k), bias.",
        },
        {
            "difficulty": "expert",
            "question": "Design a federated learning system for training a disease-prediction model across hospitals without sharing patient data.",
            "ideal_hint": "Differential privacy, secure aggregation, non-IID data, communication efficiency.",
        },
    ],
    "finance": [
        {
            "difficulty": "easy",
            "question": "What is the fundamental difference between a stock and a bond?",
            "ideal_hint": "Equity vs debt; ownership vs creditor; risk/return profile.",
        },
        {
            "difficulty": "medium",
            "question": "How would you build a real-time fraud detection system for card transactions?",
            "ideal_hint": "Feature engineering (velocity, geography), class imbalance (SMOTE), streaming inference, false-positive cost.",
        },
        {
            "difficulty": "hard",
            "question": "Walk me through building and validating a credit risk scorecard.",
            "ideal_hint": "Logistic regression baseline, WoE/IV feature selection, KS statistic, Gini, PSI for stability.",
        },
        {
            "difficulty": "expert",
            "question": "How would you architect a low-latency algorithmic trading system?",
            "ideal_hint": "Co-location, kernel bypass networking (DPDK/RDMA), lock-free queues, FPGA, market impact modelling.",
        },
    ],
    "default": [
        {
            "difficulty": "easy",
            "question": "Describe a challenging problem you solved and your approach to it.",
            "ideal_hint": "STAR method — Situation, Task, Action, Result.",
        },
        {
            "difficulty": "medium",
            "question": "How do you prioritise competing tasks under a tight deadline?",
            "ideal_hint": "Impact/urgency matrix, stakeholder communication, delegation.",
        },
    ],
}


def get_few_shot_text(domain: str, difficulty: str, n: int = 2) -> str:
    """Return formatted few-shot examples for the given domain and difficulty."""
    bank = FEW_SHOT_EXAMPLES.get(domain, FEW_SHOT_EXAMPLES["default"])
    filtered = [e for e in bank if e["difficulty"] == difficulty]
    if not filtered:
        filtered = bank
    selected = filtered[:n]
    return "\n".join(
        f"Example {i + 1}:\n  Q: {e['question']}\n  Ideal hint: {e['ideal_hint']}"
        for i, e in enumerate(selected)
    )
