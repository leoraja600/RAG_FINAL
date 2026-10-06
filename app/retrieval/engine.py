from __future__ import annotations

import os
import re
from typing import List, Dict, Any

import networkx as nx
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

from app.core.config import (
    EMBEDDING_MODEL,
    TOP_K,
)


class RetrievalEngine:
    """
    EKI-Agent Hybrid Retrieval Engine

    Retrieval:
        1. Dense semantic search
        2. Sparse BM25 search
        3. Lightweight graph/entity signal
        4. Extraction-confidence weighting
        5. Permission-aware retrieval
    """

    def __init__(self):

        print(
            f"[EKI] Loading embedding model: "
            f"{EMBEDDING_MODEL}"
        )

        self.model = SentenceTransformer(
            EMBEDDING_MODEL
        )

        self.dimension = (
            self.model.get_sentence_embedding_dimension()
        )

        # =====================================================
        # QDRANT
        # =====================================================

        qdrant_path = os.path.join(
            os.getcwd(),
            "qdrant"
        )

        os.makedirs(
            qdrant_path,
            exist_ok=True
        )

        self.qdrant = QdrantClient(
            path=qdrant_path
        )

        self.collection_name = "eki_chunks"

        self._ensure_collection()

        # =====================================================
        # LOCAL CHUNK STORE
        # =====================================================

        self.chunks: List[Dict[str, Any]] = []

        # =====================================================
        # BM25
        # =====================================================

        self.bm25 = None
        self.bm25_tokens = []

        # =====================================================
        # KNOWLEDGE GRAPH
        # =====================================================

        self.graph = nx.Graph()

    # =========================================================
    # QDRANT COLLECTION
    # =========================================================

    def _ensure_collection(self):

        try:

            collections = (
                self.qdrant
                .get_collections()
            )

            existing = {
                collection.name
                for collection in collections.collections
            }

            if self.collection_name not in existing:

                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE,
                    ),
                )

        except Exception as exc:

            print(
                f"[EKI] Qdrant initialization warning: {exc}"
            )

    # =========================================================
    # TOKENIZATION
    # =========================================================

    @staticmethod
    def _tokenize(text: str):

        text = str(text or "").lower()

        return re.findall(
            r"[a-zA-Z0-9₹$€£.%]+",
            text
        )

    # =========================================================
    # ENTITY EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_entities(text: str):

        if not text:
            return []

        entities = re.findall(
            r"\b[A-Z][A-Za-z0-9&.-]{2,}"
            r"(?:\s+[A-Z][A-Za-z0-9&.-]{2,}){0,3}",
            text,
        )

        cleaned = []

        for entity in entities:

            entity = entity.strip()

            if len(entity) >= 3:
                cleaned.append(entity)

        return list(
            dict.fromkeys(cleaned)
        )

    # =========================================================
    # PERMISSION
    # =========================================================

    @staticmethod
    def _has_permission(
        chunk: Dict[str, Any],
        user_role: str,
    ):

        access = (
            chunk.get("access_level")
            or chunk.get("access")
            or "public"
        )

        access = str(
            access
        ).lower()

        user_role = str(
            user_role
        ).lower()

        # Admin
        if user_role == "admin":
            return True

        # Public
        if access == "public":
            return True

        # Same department
        if access == user_role:
            return True

        return False

    # =========================================================
    # ADD CHUNKS
    # =========================================================

    def add(self, chunks):

        if not chunks:
            return 0

        normalized = []

        # -----------------------------------------------------
        # Normalize chunks
        # -----------------------------------------------------

        for chunk in chunks:

            if hasattr(
                chunk,
                "model_dump"
            ):

                item = chunk.model_dump()

            elif hasattr(
                chunk,
                "dict"
            ):

                item = chunk.dict()

            elif isinstance(
                chunk,
                dict
            ):

                item = dict(chunk)

            elif hasattr(
                chunk,
                "__dict__"
            ):

                item = dict(chunk.__dict__)

            else:

                item = {
                    "text": str(chunk)
                }

            item.setdefault(
                "text",
                ""
            )

            item.setdefault(
                "source",
                "unknown"
            )

            item.setdefault(
                "page",
                ""
            )

            item.setdefault(
                "modality",
                "text"
            )

            item.setdefault(
                "access_level",
                "public"
            )

            item.setdefault(
                "extraction_confidence",
                1.0
            )

            normalized.append(item)

        if not normalized:
            return 0

        # -----------------------------------------------------
        # Texts
        # -----------------------------------------------------

        texts = [
            str(
                item.get(
                    "text",
                    ""
                )
            )
            for item in normalized
        ]

        # -----------------------------------------------------
        # Embeddings
        # -----------------------------------------------------

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # -----------------------------------------------------
        # Starting index
        # -----------------------------------------------------

        start_index = len(
            self.chunks
        )

        # -----------------------------------------------------
        # Store chunks + graph
        # -----------------------------------------------------

        for offset, item in enumerate(
            normalized
        ):

            chunk_id = (
                start_index
                + offset
            )

            item["_id"] = chunk_id

            self.chunks.append(
                item
            )

            chunk_node = (
                f"chunk_{chunk_id}"
            )

            self.graph.add_node(
                chunk_node,
                chunk_id=chunk_id,
            )

            entities = (
                self._extract_entities(
                    item.get(
                        "text",
                        ""
                    )
                )
            )

            for entity in entities:

                entity_node = (
                    "entity_"
                    + entity.lower()
                )

                self.graph.add_node(
                    entity_node,
                    type="entity",
                    name=entity,
                )

                self.graph.add_edge(
                    chunk_node,
                    entity_node,
                )

        # -----------------------------------------------------
        # Qdrant points
        # -----------------------------------------------------

        points = []

        for offset, vector in enumerate(
            embeddings
        ):

            chunk_id = (
                start_index
                + offset
            )

            payload = dict(
                normalized[offset]
            )

            payload["_id"] = chunk_id

            points.append(
                PointStruct(
                    id=chunk_id,
                    vector=vector.tolist(),
                    payload=payload,
                )
            )

        if points:

            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points,
            )

        # -----------------------------------------------------
        # BM25
        # -----------------------------------------------------

        self._rebuild_bm25()

        print(
            f"[EKI] Indexed "
            f"{len(normalized)} chunk(s). "
            f"Total chunks: "
            f"{len(self.chunks)}"
        )

        return len(normalized)

    # =========================================================
    # COMPATIBILITY ALIASES
    # =========================================================

    def index(self, chunks):

        return self.add(
            chunks
        )

    def index_chunks(self, chunks):

        return self.add(
            chunks
        )

    # =========================================================
    # BM25
    # =========================================================

    def _rebuild_bm25(self):

        self.bm25_tokens = [
            self._tokenize(
                chunk.get(
                    "text",
                    ""
                )
            )
            for chunk in self.chunks
        ]

        if self.bm25_tokens:

            self.bm25 = BM25Okapi(
                self.bm25_tokens
            )

        else:

            self.bm25 = None

    # =========================================================
    # DENSE SEARCH
    # =========================================================

    def _dense_scores(
        self,
        query: str,
        allowed_indices: set,
    ):

        if not allowed_indices:
            return {}

        query_vector = self.model.encode(
            query,
            normalize_embeddings=True,
        ).tolist()

        try:

            result = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=max(
                    TOP_K * 4,
                    20
                ),
                with_payload=True,
            )

            points = result.points

        except AttributeError:

            result = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=max(
                    TOP_K * 4,
                    20
                ),
                with_payload=True,
            )

            points = result

        scores = {}

        for point in points:

            try:
                index = int(
                    point.id
                )
            except Exception:
                continue

            if index not in allowed_indices:
                continue

            scores[index] = float(
                point.score
            )

        return scores

    # =========================================================
    # BM25 SEARCH
    # =========================================================

    def _sparse_scores(
        self,
        query: str,
        allowed_indices: set,
    ):

        if self.bm25 is None:
            return {}

        tokens = self._tokenize(
            query
        )

        if not tokens:
            return {}

        raw_scores = (
            self.bm25.get_scores(
                tokens
            )
        )

        scores = {}

        if len(raw_scores):

            max_score = max(
                raw_scores
            )

        else:

            max_score = 0.0

        for index, score in enumerate(
            raw_scores
        ):

            if index not in allowed_indices:
                continue

            if max_score > 0:

                normalized = (
                    float(score)
                    / float(max_score)
                )

            else:

                normalized = 0.0

            scores[index] = normalized

        return scores

    # =========================================================
    # GRAPH SEARCH
    # =========================================================

    def _graph_scores(
        self,
        query: str,
        allowed_indices: set,
    ):

        if not allowed_indices:
            return {}

        query_entities = (
            self._extract_entities(
                query
            )
        )

        if not query_entities:
            return {}

        scores = {}

        for index in allowed_indices:

            chunk_node = (
                f"chunk_{index}"
            )

            if chunk_node not in self.graph:
                continue

            score = 0.0

            for entity in query_entities:

                entity_node = (
                    "entity_"
                    + entity.lower()
                )

                if (
                    entity_node in self.graph
                    and self.graph.has_edge(
                        chunk_node,
                        entity_node,
                    )
                ):

                    score += 1.0

            if score > 0:

                scores[index] = min(
                    score
                    / len(query_entities),
                    1.0,
                )

        return scores

    # =========================================================
    # MAIN SEARCH
    # =========================================================

    def search(
        self,
        query: str,
        user_role: str = "public",
        top_k: int | None = None,
    ):

        if top_k is None:
            top_k = TOP_K

        if not self.chunks:
            return []

        # -----------------------------------------------------
        # Permission filtering
        # -----------------------------------------------------

        allowed_indices = {
            index
            for index, chunk in enumerate(
                self.chunks
            )
            if self._has_permission(
                chunk,
                user_role
            )
        }

        if not allowed_indices:
            return []

        # -----------------------------------------------------
        # Retrieval
        # -----------------------------------------------------

        dense_scores = (
            self._dense_scores(
                query,
                allowed_indices,
            )
        )

        sparse_scores = (
            self._sparse_scores(
                query,
                allowed_indices,
            )
        )

        graph_scores = (
            self._graph_scores(
                query,
                allowed_indices,
            )
        )

        # -----------------------------------------------------
        # Candidate set
        # -----------------------------------------------------

        candidates = set()

        candidates.update(
            dense_scores.keys()
        )

        candidates.update(
            sparse_scores.keys()
        )

        candidates.update(
            graph_scores.keys()
        )

        scored = []

        # -----------------------------------------------------
        # Hybrid scoring
        # -----------------------------------------------------

        for index in candidates:

            dense = dense_scores.get(
                index,
                0.0
            )

            sparse = sparse_scores.get(
                index,
                0.0
            )

            graph = graph_scores.get(
                index,
                0.0
            )

            hybrid = (
                0.55 * dense
                + 0.30 * sparse
                + 0.15 * graph
            )

            confidence = (
                self.chunks[index].get(
                    "extraction_confidence",
                    1.0
                )
            )

            try:

                confidence = float(
                    confidence
                )

            except Exception:

                confidence = 1.0

            confidence = max(
                0.0,
                min(
                    confidence,
                    1.0
                ),
            )

            final_score = (
                hybrid
                * confidence
            )

            scored.append(
                (
                    index,
                    final_score,
                    dense,
                    sparse,
                    graph,
                )
            )

        # -----------------------------------------------------
        # Sort
        # -----------------------------------------------------

        scored.sort(
            key=lambda x: x[1],
            reverse=True
        )

        # -----------------------------------------------------
        # Return results
        # -----------------------------------------------------

        results = []

        for (
            index,
            score,
            dense,
            sparse,
            graph,
        ) in scored[:top_k]:

            result = dict(
                self.chunks[index]
            )

            result["score"] = round(
                float(score),
                4
            )

            result["dense_score"] = round(
                float(dense),
                4
            )

            result["sparse_score"] = round(
                float(sparse),
                4
            )

            result["graph_score"] = round(
                float(graph),
                4
            )

            results.append(
                result
            )

        return results

    # =========================================================
    # CLEAR
    # =========================================================

    def clear(self):

        self.chunks.clear()

        self.bm25 = None
        self.bm25_tokens.clear()

        self.graph.clear()

        try:

            self.qdrant.delete_collection(
                self.collection_name
            )

        except Exception:
            pass

        self._ensure_collection()

        print(
            "[EKI] Retrieval index cleared."
        )