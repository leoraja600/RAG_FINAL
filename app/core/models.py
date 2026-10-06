from dataclasses import dataclass, field
from typing import Any

@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    page: int | None = None
    modality: str = "text"
    source: str = ""
    access_level: str = "public"
    extraction_confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Evidence:
    chunk: Chunk
    score: float
    dense_score: float = 0.0
    sparse_score: float = 0.0
    graph_score: float = 0.0

@dataclass
class AgentTrace:
    agent: str
    action: str
    input_summary: str
    output_summary: str

@dataclass
class QueryResult:
    answer: str
    citations: list[dict[str, Any]]
    traces: list[AgentTrace]
    iterations: int
    critic: dict[str, Any]
