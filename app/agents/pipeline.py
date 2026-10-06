import json
import re
from typing import Any

from app.agents.llm import llm
from app.core.config import MAX_RETRIES, TOP_K, LLM_PROVIDER
from app.core.models import AgentTrace, QueryResult
from app.core.store import log, save_query


class AgentPipeline:
    """
    EKI-Agent pipeline:

    Planner
        ↓
    Researcher
        ↓
    Writer
        ↓
    Critic
        ↓
    Self-Correction / Re-retrieval
        ↓
    Final Answer + Citations
    """

    def __init__(self, retriever):
        self.retriever = retriever

    # =========================================================
    # GENERIC HELPERS
    # =========================================================

    def _get(self, obj: Any, key: str, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)

    def _chunk(self, item):
        """
        Supports:

            Evidence(chunk=Chunk(...))

        and:

            {
                "text": "...",
                "source": "..."
            }

        and:

            {
                "chunk": {...}
            }
        """

        if isinstance(item, dict):

            nested = item.get("chunk")

            if nested is not None:
                return nested

            return item

        nested = getattr(item, "chunk", None)

        if nested is not None:
            return nested

        return item

    def _text(self, item) -> str:

        chunk = self._chunk(item)

        value = self._get(
            chunk,
            "text",
            ""
        )

        if value is None:
            return ""

        return str(value).strip()

    def _source(self, item) -> str:

        chunk = self._chunk(item)

        source = (
            self._get(chunk, "source")
            or self._get(chunk, "filename")
            or self._get(chunk, "file_name")
            or self._get(chunk, "document_name")
            or self._get(chunk, "document")
            or "Unknown document"
        )

        return str(source)

    def _page(self, item):

        chunk = self._chunk(item)

        return (
            self._get(chunk, "page")
            or self._get(chunk, "page_number")
            or self._get(chunk, "page_no")
        )

    def _modality(self, item) -> str:

        chunk = self._chunk(item)

        return str(
            self._get(chunk, "modality")
            or self._get(chunk, "type")
            or "text"
        )

    def _score(self, item) -> float:

        value = self._get(
            item,
            "score",
            0.0
        )

        try:
            return float(value or 0.0)

        except Exception:
            return 0.0

    def _chunk_id(self, item) -> str:

        chunk = self._chunk(item)

        return str(
            self._get(
                chunk,
                "chunk_id",
                ""
            )
        )

    # =========================================================
    # TERM EXTRACTION
    # =========================================================

    def _terms(self, text: str):

        stopwords = {
            "what",
            "was",
            "were",
            "is",
            "are",
            "the",
            "a",
            "an",
            "of",
            "in",
            "on",
            "for",
            "to",
            "from",
            "and",
            "or",
            "who",
            "which",
            "how",
            "much",
            "many",
            "does",
            "did",
            "do",
            "with",
            "by",
            "this",
            "that",
            "their",
            "its",
            "about",
            "tell",
            "me",
            "please",
            "can",
            "could",
            "would",
            "should",
            "explain",
            "give",
            "show",
            "find",
            "according",
            "based",
            "2023",
            "2024",
            "2025",
            "2026",
            "confidential",
        }

        words = re.findall(
            r"[a-zA-Z0-9]+",
            str(text).lower()
        )

        return {
            word
            for word in words
            if word not in stopwords
            and len(word) > 2
        }

    # =========================================================
    # SENTENCE SPLITTER
    # =========================================================

    def _sentences(self, text: str):

        cleaned = re.sub(
            r"\s+",
            " ",
            str(text or "")
        ).strip()

        if not cleaned:
            return []

        return [
            sentence.strip()
            for sentence in re.split(
                r"(?<=[.!?])\s+",
                cleaned
            )
            if sentence.strip()
        ]

    # =========================================================
    # VALUE DETECTION
    # =========================================================

    def _contains_value(self, text: str) -> bool:

        pattern = re.compile(
            r"(?:"
            r"\b\d+(?:\.\d+)?\s*%"
            r"|"
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:lakh|lakhs|crore|crores|"
            r"million|billion|thousand|"
            r"inr|usd|eur|gbp)\b"
            r"|"
            r"[$€£₹]\s*"
            r"\d+(?:,\d{3})*(?:\.\d+)?"
            r"|"
            r"\b\d+(?:,\d{3})+(?:\.\d+)?\b"
            r")",
            re.IGNORECASE,
        )

        return bool(
            pattern.search(
                str(text)
            )
        )

    # =========================================================
    # BEST ANSWER SENTENCE
    # =========================================================

    def _best_sentence(
        self,
        query: str,
        evidence_text: str
    ):

        query_terms = self._terms(query)

        if not query_terms:

            sentences = self._sentences(
                evidence_text
            )

            return (
                sentences[0]
                if sentences
                else None
            )

        query_lower = query.lower().strip(
            " ?."
        )

        candidates = []

        for index, sentence in enumerate(
            self._sentences(evidence_text)
        ):

            sentence_lower = sentence.lower()

            sentence_terms = self._terms(
                sentence
            )

            overlap = len(
                query_terms &
                sentence_terms
            )

            phrase_bonus = 0

            compact_query = re.sub(
                r"\s+",
                " ",
                query_lower
            )

            if (
                compact_query
                and compact_query in sentence_lower
            ):
                phrase_bonus += 5

            # Special handling:
            #
            # What is the Financial Stability Report?
            #
            # → Financial Stability Report

            if query_lower.startswith(
                "what is "
            ):

                subject = (
                    query_lower[8:]
                    .strip(" ?.")
                )

                if (
                    subject
                    and subject in sentence_lower
                ):
                    phrase_bonus += 5

            value_bonus = (
                2
                if self._contains_value(
                    sentence
                )
                else 0
            )

            length_penalty = min(
                len(sentence) / 500.0,
                1.0
            )

            score = (
                overlap * 3
                + phrase_bonus
                + value_bonus
                - length_penalty
            )

            candidates.append(
                (
                    score,
                    overlap,
                    -index,
                    sentence,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            reverse=True
        )

        return candidates[0][3]

    # =========================================================
    # SUPPORTING SENTENCE
    # =========================================================

    def _supporting_sentence(
        self,
        query: str,
        evidence_text: str,
        primary: str | None
    ):

        query_terms = self._terms(query)

        candidates = []

        for index, sentence in enumerate(
            self._sentences(evidence_text)
        ):

            if (
                primary
                and sentence == primary
            ):
                continue

            overlap = len(
                query_terms &
                self._terms(sentence)
            )

            if overlap > 0:

                candidates.append(
                    (
                        overlap,
                        -index,
                        sentence,
                    )
                )

        candidates.sort(
            reverse=True
        )

        return (
            candidates[0][2]
            if candidates
            else None
        )

    # =========================================================
    # PLANNER AGENT
    # =========================================================

    def planner(
        self,
        query,
        user_role,
        traces
    ):

        query_lower = query.lower()

        intent = (
            "multi-hop"
            if any(
                word in query_lower
                for word in [
                    " and ",
                    " why ",
                    "compare",
                    "relationship",
                    "responsible",
                ]
            )
            else "lookup"
        )

        plan = {
            "intent": intent,
            "steps": [
                "retrieve relevant evidence",
                "check permissions",
                "verify evidence sufficiency",
                "synthesize grounded answer",
                "critic verification",
            ],
        }

        traces.append(
            AgentTrace(
                "Planner",
                "plan",
                query,
                str(plan),
            )
        )

        log(
            user_role,
            "Planner",
            "plan",
            query,
            str(plan),
        )

        return plan

    # =========================================================
    # RESEARCHER AGENT
    # =========================================================

    def researcher(
        self,
        query,
        user_role,
        traces
    ):

        try:

            evidence = self.retriever.search(
                query=query,
                user_role=user_role,
                top_k=TOP_K,
            )

        except TypeError:

            try:

                evidence = self.retriever.search(
                    query,
                    user_role,
                    TOP_K,
                )

            except TypeError:

                evidence = self.retriever.search(
                    query,
                    user_role,
                )

        evidence = evidence or []

        scores = [
            round(
                self._score(item),
                3
            )
            for item in evidence[:5]
        ]

        summary = (
            f"retrieved={len(evidence)}; "
            f"top_scores={scores}"
        )

        traces.append(
            AgentTrace(
                "Researcher",
                "retrieve",
                query,
                summary,
            )
        )

        log(
            user_role,
            "Researcher",
            "retrieve",
            query,
            summary,
        )

        return evidence

    # =========================================================
    # DETERMINISTIC WRITER
    # =========================================================

    def _deterministic_answer(
        self,
        query,
        evidence
    ):

        if not evidence:

            return (
                "I could not find sufficient evidence "
                "in the authorized enterprise documents "
                "to answer this question."
            )

        texts = [
            self._text(item)
            for item in evidence
            if self._text(item)
        ]

        if not texts:

            return (
                "Relevant evidence was retrieved, "
                "but it contained no readable text."
            )

        evidence_text = " ".join(
            texts
        )

        primary = self._best_sentence(
            query,
            evidence_text,
        )

        supporting = self._supporting_sentence(
            query,
            evidence_text,
            primary,
        )

        if primary:

            answer = primary

            if (
                supporting
                and supporting != primary
                and len(answer) < 420
            ):

                answer += (
                    " "
                    + supporting
                )

            return answer

        return texts[0]

    # =========================================================
    # WRITER AGENT
    # =========================================================

    def writer(
        self,
        query,
        evidence,
        user_role,
        traces
    ):

        if not evidence:

            answer = (
                "I could not find sufficient evidence "
                "in the authorized enterprise documents "
                "to answer this question."
            )

            traces.append(
                AgentTrace(
                    "Writer",
                    "generate",
                    query,
                    answer,
                )
            )

            log(
                user_role,
                "Writer",
                "generate",
                query,
                answer,
            )

            return answer

        # -----------------------------------------------------
        # Build evidence blocks for optional LLM
        # -----------------------------------------------------

        blocks = []

        for index, item in enumerate(
            evidence,
            1
        ):

            blocks.append(
                f"[EVIDENCE {index}]\n"
                f"TEXT: {self._text(item)}\n"
                f"SOURCE: {self._source(item)}\n"
                f"PAGE: {self._page(item) or '-'}\n"
                f"MODALITY: {self._modality(item)}"
            )

        deterministic = (
            self._deterministic_answer(
                query,
                evidence,
            )
        )

        provider = (
            LLM_PROVIDER
            or "none"
        ).lower()

        llm_enabled = False

        try:
            llm_enabled = bool(
                llm.enabled()
            )
        except Exception:
            llm_enabled = False

        # =====================================================
        # NO LLM
        # =====================================================

        if (
            provider in {
                "",
                "none",
                "null",
            }
            or not llm_enabled
        ):

            answer = deterministic

        # =====================================================
        # LLM
        # =====================================================

        else:

            prompt = (
                "You are the Writer agent of an "
                "enterprise multimodal RAG system.\n\n"

                f"QUESTION:\n{query}\n\n"

                "AUTHORIZED EVIDENCE:\n"
                + "\n\n".join(blocks)

                + "\n\nRULES:\n"

                "1. Use only the authorized evidence.\n"

                "2. Answer the actual question "
                "directly in natural language.\n"

                "3. Never output Python representations "
                "such as Chunk(...) or Evidence(...).\n"

                "4. Do not invent facts.\n"

                "5. If the evidence supports a direct "
                "answer, state it clearly.\n"

                "6. Mention the source when useful.\n"

                "7. If evidence is genuinely insufficient, "
                "say so.\n"

                "8. Keep the answer concise."
            )

            generated = (
                llm.complete(
                    prompt
                )
                or ""
            )

            answer = (
                generated.strip()
                if generated.strip()
                else deterministic
            )

            refusal_phrases = [
                "insufficient evidence",
                "cannot be determined",
                "not available",
                "not provided",
                "not enough information",
            ]

            if (
                any(
                    phrase in answer.lower()
                    for phrase in refusal_phrases
                )
                and deterministic
            ):

                answer = deterministic

        traces.append(
            AgentTrace(
                "Writer",
                "generate",
                query,
                answer[:1000],
            )
        )

        log(
            user_role,
            "Writer",
            "generate",
            query,
            answer[:2000],
        )

        return answer

    # =========================================================
    # RELEVANCE
    # =========================================================

    def _calculate_relevance(
        self,
        query,
        answer,
        evidence
    ):

        query_terms = self._terms(
            query
        )

        if not query_terms:
            return 0.0

        answer_terms = self._terms(
            answer
        )

        evidence_terms = self._terms(
            " ".join(
                self._text(item)
                for item in evidence
            )
        )

        answer_overlap = (
            len(
                query_terms &
                answer_terms
            )
            /
            max(
                1,
                len(query_terms)
            )
        )

        evidence_overlap = (
            len(
                query_terms &
                evidence_terms
            )
            /
            max(
                1,
                len(query_terms)
            )
        )

        query_lower = (
            query.lower()
            .strip(" ?.")
        )

        answer_lower = str(
            answer
        ).lower()

        phrase_bonus = 0.0

        if (
            query_lower
            and query_lower in answer_lower
        ):

            phrase_bonus = 0.20

        elif (
            query_lower.startswith(
                "what is "
            )
            and query_lower[8:].strip()
            in answer_lower
        ):

            phrase_bonus = 0.20

        relevance = (
            0.65 * answer_overlap
            +
            0.35 * evidence_overlap
            +
            phrase_bonus
        )

        return round(
            min(
                1.0,
                relevance
            ),
            2,
        )

    # =========================================================
    # GROUNDEDNESS
    # =========================================================

    def _calculate_groundedness(
        self,
        answer,
        evidence
    ):

        answer_terms = self._terms(
            answer
        )

        evidence_terms = self._terms(
            " ".join(
                self._text(item)
                for item in evidence
            )
        )

        if not answer_terms:
            return 0.0

        groundedness = (
            len(
                answer_terms &
                evidence_terms
            )
            /
            len(answer_terms)
        )

        return round(
            min(
                1.0,
                groundedness
            ),
            2,
        )

    # =========================================================
    # DIRECT SUPPORT
    # =========================================================

    def _direct_support(
        self,
        query,
        evidence
    ):

        query_terms = self._terms(
            query
        )

        if not query_terms:
            return False

        required_overlap = max(
            1,
            min(
                2,
                len(query_terms)
            )
        )

        for item in evidence:

            for sentence in self._sentences(
                self._text(item)
            ):

                overlap = len(
                    query_terms &
                    self._terms(sentence)
                )

                if overlap >= required_overlap:
                    return True

        return False

    # =========================================================
    # CRITIC AGENT
    # =========================================================

    def critic(
        self,
        query,
        evidence,
        answer,
        user_role,
        traces
    ):

        if not evidence:

            result = {
                "sufficient": False,
                "passed": False,
                "groundedness": 0.0,
                "relevance": 0.0,
                "reason": (
                    "No authorized evidence was retrieved "
                    "for this user role."
                ),
                "missing": (
                    "relevant supporting evidence"
                ),
            }

        else:

            relevance = (
                self._calculate_relevance(
                    query,
                    answer,
                    evidence,
                )
            )

            groundedness = (
                self._calculate_groundedness(
                    answer,
                    evidence,
                )
            )

            direct_support = (
                self._direct_support(
                    query,
                    evidence,
                )
            )

            max_score = max(
                (
                    self._score(item)
                    for item in evidence
                ),
                default=0.0,
            )

            sufficient = bool(
                direct_support
                and max_score >= 0.20
                and groundedness >= 0.45
                and relevance >= 0.25
            )

            result = {
                "sufficient": sufficient,
                "passed": sufficient,
                "groundedness": groundedness,
                "relevance": relevance,
                "reason": (
                    "Direct supporting evidence was found "
                    "in the authorized enterprise documents."
                    if sufficient
                    else
                    "The retrieved evidence does not yet "
                    "provide enough direct support for the "
                    "generated answer."
                ),
                "missing": (
                    ""
                    if sufficient
                    else
                    "specific supporting evidence or "
                    "a better grounded answer"
                ),
            }

        traces.append(
            AgentTrace(
                "Critic",
                "evaluate",
                query,
                json.dumps(result),
            )
        )

        log(
            user_role,
            "Critic",
            "evaluate",
            query,
            json.dumps(result),
        )

        return result

    # =========================================================
    # SELF-CORRECTION
    # =========================================================

    def _self_correct(
        self,
        query,
        critic
    ):

        missing = (
            critic.get("missing")
            or "specific supporting evidence"
        )

        return (
            f"{query}. "
            f"Find specific authoritative evidence for: "
            f"{missing}"
        )

    # =========================================================
    # CITATIONS
    # =========================================================

    def _build_citations(
        self,
        evidence
    ):

        citations = []
        seen = set()

        for item in evidence:

            text = self._text(
                item
            )

            source = self._source(
                item
            )

            page = self._page(
                item
            )

            modality = self._modality(
                item
            )

            score = self._score(
                item
            )

            chunk_id = self._chunk_id(
                item
            )

            key = (
                source,
                page,
                modality,
                chunk_id
                or text[:120],
            )

            if key in seen:
                continue

            seen.add(key)

            citations.append(
                {
                    "source": source,
                    "page": page,
                    "modality": modality,
                    "score": round(
                        score,
                        3,
                    ),
                    "chunk_id": chunk_id,
                    "text": text,
                }
            )

        return citations

    # =========================================================
    # MAIN PIPELINE
    # =========================================================

    def run(
        self,
        query,
        user_role="admin"
    ):

        traces = []

        # -----------------------------------------------------
        # Planner
        # -----------------------------------------------------

        self.planner(
            query,
            user_role,
            traces,
        )

        current_query = query

        final_answer = ""

        critic_result = {}

        evidence = []

        iterations = 0

        # -----------------------------------------------------
        # Agentic loop
        # -----------------------------------------------------

        for iteration in range(
            MAX_RETRIES + 1
        ):

            iterations = (
                iteration + 1
            )

            # Researcher
            evidence = (
                self.researcher(
                    current_query,
                    user_role,
                    traces,
                )
            )

            # Writer
            final_answer = (
                self.writer(
                    query,
                    evidence,
                    user_role,
                    traces,
                )
            )

            # Critic
            critic_result = (
                self.critic(
                    query,
                    evidence,
                    final_answer,
                    user_role,
                    traces,
                )
            )

            # Passed
            if critic_result.get(
                "sufficient",
                False
            ):
                break

            # No more retries
            if iteration >= MAX_RETRIES:
                break

            # Self-correction
            current_query = (
                self._self_correct(
                    query,
                    critic_result,
                )
            )

            message = (
                "Critic found insufficient evidence. "
                "Retrying retrieval with: "
                f"{current_query}"
            )

            traces.append(
                AgentTrace(
                    "Self-Correction",
                    "reformulate",
                    current_query,
                    message,
                )
            )

            log(
                user_role,
                "Self-Correction",
                "reformulate",
                query,
                current_query,
            )

        # -----------------------------------------------------
        # Keep the readable answer.
        #
        # The critic result is displayed separately.
        # -----------------------------------------------------

        if not final_answer:

            final_answer = (
                "I could not generate an answer "
                "from the available evidence."
            )

        # -----------------------------------------------------
        # Citations
        # -----------------------------------------------------

        citations = (
            self._build_citations(
                evidence
            )
        )

        # -----------------------------------------------------
        # Save audit/query record
        # -----------------------------------------------------

        save_query(
            user_role,
            query,
            final_answer,
            iterations,
        )

        # -----------------------------------------------------
        # Return
        # -----------------------------------------------------

        return QueryResult(
            final_answer,
            citations,
            traces,
            iterations,
            critic_result,
        )