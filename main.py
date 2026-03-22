import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Comma-separated origins, e.g. "http://localhost:3000,https://vectorshift-clone.netlify.app"
# Set ALLOWED_ORIGINS on your host (Render/Railway) when you deploy the backend.
_default_origins = "http://localhost:3000,https://vectorshift-clone.netlify.app"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Edge(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class Node(BaseModel):
    id: str
    type: str
    position: Optional[dict] = None
    data: Optional[dict] = None


class PipelineRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class PipelineParseResponse(BaseModel):
    """API response: JSON uses true/false for is_dag (not strings)."""

    num_nodes: int
    num_edges: int
    is_dag: bool


def is_dag(nodes: List[dict], edges: List[dict]) -> bool:
    """Check if the graph formed by nodes and edges is a directed acyclic graph (DAG)."""
    node_ids = {n["id"] for n in nodes}
    if not node_ids:
        return True

    # Build adjacency list
    adj = {nid: [] for nid in node_ids}
    for e in edges:
        src, tgt = e.get("source"), e.get("target")
        if src in node_ids and tgt in node_ids:
            adj[src].append(tgt)

    # Kahn's algorithm / DFS for cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in node_ids}

    def has_cycle(u):
        color[u] = GRAY
        for v in adj[u]:
            if color[v] == GRAY:
                return True
            if color[v] == WHITE and has_cycle(v):
                return True
        color[u] = BLACK
        return False

    for nid in node_ids:
        if color[nid] == WHITE and has_cycle(nid):
            return False
    return True


@app.get("/")
def read_root():
    return {"Ping": "Pong"}


@app.post("/pipelines/parse", response_model=PipelineParseResponse)
def parse_pipeline(pipeline: PipelineRequest) -> PipelineParseResponse:
    nodes = [{"id": n.id} for n in pipeline.nodes]
    edges = [{"source": e.source, "target": e.target} for e in pipeline.edges]

    num_nodes = len(nodes)
    num_edges = len(edges)
    # Explicit bool for DAG check (JSON: true / false)
    is_dag_value: bool = bool(is_dag(nodes, edges))

    return PipelineParseResponse(
        num_nodes=num_nodes,
        num_edges=num_edges,
        is_dag=is_dag_value,
    )
