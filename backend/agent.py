"""
AI Interview Avatar Agent — Main Entry Point

Architecture:
  LiveKit agent (STT → OpenAI LLM → TTS → Avatar)
    ├── NLP Preprocessor  : cleans + tokenises every user turn
    ├── RAG Retriever      : semantic search over Pinecone knowledge base
    ├── Question Generator : few-shot + RAG-informed question creation
    ├── Answer Evaluator   : chain-of-thought scoring (3 dimensions)
    └── Session Manager    : state machine tracking the full interview

Supported domains (set via room metadata JSON: {"domain": "healthcare"}):
  software_engineering | healthcare | finance
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, RoomOutputOptions
from livekit.plugins import anam, cartesia, deepgram, openai as lk_openai, noise_cancellation, silero

from interview.evaluator import AnswerEvaluator
from interview.question_generator import QuestionGenerator
from interview.session_manager import InterviewSessionManager
from nlp.preprocessor import TextPreprocessor
from prompts.templates import FINAL_REPORT_PROMPT, INTERVIEWER_SYSTEM_PROMPT
from rag.retriever import KnowledgeRetriever

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_DOMAINS = {"software_engineering", "healthcare", "finance"}
DEFAULT_DOMAIN = "software_engineering"

# At most one follow-up probe per question, so the interview keeps moving.
MAX_FOLLOWUPS_PER_QUESTION = 1

_CLARIFY_PATTERNS = (
    "repeat", "say that again", "say again", "didn't catch", "did not catch", "pardon",
    "come again", "what do you mean", "can you clarify", "could you clarify", "rephrase",
    "what was the question", "what's the question", "didn't hear", "did not hear",
)
_GIVE_UP_PATTERNS = (
    "don't know", "dont know", "do not know", "not sure", "no idea", "no clue",
    "can't answer", "cant answer", "cannot answer", "skip this", "pass on this", "i pass",
)


def _is_clarification(text: str) -> bool:
    """True if the candidate is asking the interviewer to repeat/clarify rather than answering."""
    t = text.lower().strip()
    if len(t.split()) > 12:
        return False
    return any(p in t for p in _CLARIFY_PATTERNS)


def _is_giving_up(text: str) -> bool:
    """True if the candidate signalled they don't know — probing further would be unkind."""
    t = text.lower().strip()
    if len(t.split()) > 14:
        return False
    return any(p in t for p in _GIVE_UP_PATTERNS)


def _should_follow_up(evaluation: dict, followups_asked: int) -> bool:
    """Probe deeper when the answer is weak or clearly missing key concepts."""
    if followups_asked >= MAX_FOLLOWUPS_PER_QUESTION:
        return False
    score = evaluation.get("overall_score", 10)
    missing = evaluation.get("key_concepts_missing") or []
    return score < 6.5 or (bool(missing) and score < 8.0)


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

class InterviewAvatar(Agent):
    """
    LiveKit agent that conducts a structured domain-specific technical interview.

    On each user turn:
      1. Pre-process the answer text (NLP pipeline).
      2. Evaluate the answer via CoT scoring.
      3. Record the result in the session.
      4. If the quota is reached → generate the verbal performance report.
      5. Otherwise → retrieve RAG context and generate the next question.
    """

    def __init__(self, domain: str = DEFAULT_DOMAIN) -> None:
        self.domain = domain
        self._intro_step = 0  # HR-style opening: 0=awaiting name, 1=awaiting self-intro, 2=done
        self.session_mgr = InterviewSessionManager(domain=domain, max_questions=8)
        self.question_gen = QuestionGenerator(domain=domain)
        self.evaluator = AnswerEvaluator()
        self.preprocessor = TextPreprocessor()
        self.retriever = KnowledgeRetriever(domain=domain)

        super().__init__(
            instructions=INTERVIEWER_SYSTEM_PROMPT.format(
                domain=domain.replace("_", " ").title()
            )
        )

    async def on_user_turn_completed(self, turn_ctx, new_message):
        user_text = new_message.text_content
        if not user_text or not self.session_mgr.is_active:
            return

        current_q = self.session_mgr.get_current_question()

        # ---- HR-style intro phase: name → self-introduction → first technical question
        if self._intro_step < 2 and self.session_mgr.question_count == 0:
            await self._handle_intro(turn_ctx)
            return

        # ---- Candidate asked us to repeat/clarify → re-ask, don't score or advance
        if current_q and _is_clarification(user_text):
            turn_ctx.add_message(
                role="system",
                content=(
                    "The candidate asked you to repeat or clarify — this is NOT an answer. "
                    "Restate the current question in simpler, clearer words, briefly and warmly. "
                    f'The current question is: "{current_q}"'
                ),
            )
            return

        # ---- Normal answer turn: preprocess + accumulate + evaluate
        processed = self.preprocessor.preprocess(user_text)
        logger.info("Keywords: %s", processed["keywords"])
        self.session_mgr.add_answer_part(processed["clean_text"])

        evaluation = await self.evaluator.evaluate(
            question=current_q,
            answer=self.session_mgr.current_answer_text(),
            domain=self.domain,
        )

        # ---- Decide: probe deeper with a follow-up, or move on
        giving_up = _is_giving_up(user_text)
        if not giving_up and _should_follow_up(evaluation, self.session_mgr.followups_asked):
            self.session_mgr.register_followup()
            missing = evaluation.get("key_concepts_missing") or []
            gap = ", ".join(missing[:2]) if missing else "the key details"
            logger.info("Q%d follow-up (gap: %s)", self.session_mgr.question_count, gap)
            turn_ctx.add_message(
                role="system",
                content=(
                    "The candidate's answer was partial — it did not fully cover: "
                    f"{gap}. Acknowledge what they said specifically and warmly, then ask ONE short, "
                    "natural follow-up that probes deeper into that gap. Reference something they "
                    "actually said. Stay on the SAME topic — do not introduce a new question yet."
                ),
            )
            return

        # ---- Answer accepted → record it and advance
        self.session_mgr.record_answer(evaluation)
        logger.info(
            "Q%d scored %.1f/10", self.session_mgr.question_count, evaluation["overall_score"]
        )

        if self.session_mgr.should_end_interview():
            self.session_mgr.is_active = False
            report = self.session_mgr.generate_report()
            verbal_cue = FINAL_REPORT_PROMPT.format(
                domain=self.domain.replace("_", " "),
                report_json=json.dumps(report, indent=2),
                recommendation=report["recommendation"],
                average_score=report["average_score"],
            )
            turn_ctx.add_message(role="system", content=verbal_cue)
            return

        context = await self.retriever.retrieve(processed["clean_text"])
        next_q = await self.question_gen.generate_next(
            session=self.session_mgr, context=context
        )
        if next_q:
            self.session_mgr.set_current_question(next_q)
            if giving_up:
                lead_in = (
                    "The candidate said they're unsure. Reassure them kindly that it's fine, then "
                    "gently move on. "
                )
            else:
                lead_in = (
                    "Acknowledge their answer in one short, specific sentence (without saying whether "
                    "it was right or wrong), then smoothly transition. "
                )
            turn_ctx.add_message(
                role="system",
                content=(
                    lead_in
                    + "Ask the next question conversationally, in your own words — you may connect it "
                    f'to the discussion so far. The next question is about: "{next_q}"'
                ),
            )

    async def _handle_intro(self, turn_ctx) -> None:
        """Run the HR-style opening before any technical questions.

        Step 0: candidate just gave their name  → greet by name, ask for a self-introduction.
        Step 1: candidate just introduced themselves → warm reaction, then ask the first question.
        """
        domain_label = self.domain.replace("_", " ")

        if self._intro_step == 0:
            self._intro_step = 1
            turn_ctx.add_message(
                role="system",
                content=(
                    "The candidate just told you their name. Greet them by name, warmly and briefly. "
                    "Then, just like the opening of a real HR interview, invite them to introduce "
                    f"themselves — their background, experience, and what draws them to this "
                    f"{domain_label} role. Ask only this for now; do NOT start technical questions yet."
                ),
            )
            return

        # Step 1 → candidate has introduced themselves; transition into technical questions.
        first_q = await self.question_gen.generate_next(session=self.session_mgr, context=[])
        if not first_q:
            return
        self.session_mgr.set_current_question(first_q)
        self._intro_step = 2
        logger.info("Intro complete — starting technical questions with Q1")
        turn_ctx.add_message(
            role="system",
            content=(
                "The candidate just introduced themselves. React warmly to something specific they "
                f"mentioned. Then let them know you'll now move into a few {domain_label} questions, "
                f'and ask your FIRST question, phrased naturally in your own words: "{first_q}"'
            ),
        )


# ---------------------------------------------------------------------------
# LiveKit entrypoint
# ---------------------------------------------------------------------------

async def entrypoint(ctx: agents.JobContext):
    logger.info("Interview agent joining room: %s", ctx.room.name)

    # Read domain from room metadata
    domain = DEFAULT_DOMAIN
    if ctx.room.metadata:
        try:
            meta = json.loads(ctx.room.metadata)
            candidate = meta.get("domain", DEFAULT_DOMAIN)
            domain = candidate if candidate in SUPPORTED_DOMAINS else DEFAULT_DOMAIN
        except (json.JSONDecodeError, TypeError):
            pass

    logger.info("Interview domain: %s", domain)

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=lk_openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
    )

    # Anam AI avatar (graceful degradation if unavailable)
    try:
        persona = anam.PersonaConfig(
            name="Interview AI",
            avatarId="edf6fdcb-acab-44b8-b974-ded72665ee26",
        )
        avatar = anam.AvatarSession(persona_config=persona)
        await avatar.start(session, room=ctx.room)
        logger.info("Anam avatar ready")
    except Exception as exc:
        logger.warning("Avatar unavailable: %s", exc)

    await session.start(
        room=ctx.room,
        agent=InterviewAvatar(domain=domain),
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
        room_output_options=RoomOutputOptions(audio_enabled=True),
    )

    domain_label = domain.replace("_", " ").title()
    await session.generate_reply(
        instructions=(
            f"Open the interview like a warm, professional HR interviewer. Greet the candidate, "
            f"introduce yourself as the AI interviewer for the {domain_label} position, and make them "
            f"feel at ease. Then ask for their name so you can get started. Keep it brief and friendly."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
