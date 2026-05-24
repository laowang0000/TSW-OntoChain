"""FastAPI application for the OntoChain semantic risk analysis MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .services.graph_service import graph_data, risk_summary
from .services.ontology_service import DATA_DIR, GENERATED_GRAPH_PATH, SAMPLE_CSV_PATH, load_generated_graph, save_graph
from .services.rdf_builder import build_graph_from_csv, triples_as_strings
from .services.reasoning_service import apply_reasoning
from .services.sparql_service import execute_sparql


app = FastAPI(
    title="OntoChain Semantic Blockchain Risk API",
    description="Builds RDF knowledge graphs from transaction CSV data, applies OWL/RDFS vocabulary and rule-based inference, and exposes SPARQL queries.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SparqlRequest(BaseModel):
    query: str


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "OntoChain",
        "message": "Use POST /build-graph, GET /triples, POST /query-sparql, GET /risk-summary, and GET /graph-data.",
    }


@app.post("/build-graph")
async def build_graph(file: Annotated[UploadFile | None, File(description="Optional transaction CSV")] = None) -> dict:
    """Build an RDF graph from an uploaded CSV or the bundled sample CSV."""

    try:
        csv_path = await _resolve_csv(file)
        graph = build_graph_from_csv(csv_path)
        apply_reasoning(graph)
        save_graph(graph, GENERATED_GRAPH_PATH)
        return {"status": "built", "source_csv": str(csv_path), "summary": risk_summary(graph)}
    except Exception as exc:  # noqa: BLE001 - API should return a readable demo error.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/triples")
def triples(limit: int = 200) -> dict[str, object]:
    graph = load_generated_graph()
    return {"triple_count": len(graph), "triples": triples_as_strings(graph, limit=limit)}


@app.post("/query-sparql")
def query_sparql(request: SparqlRequest) -> dict:
    try:
        return execute_sparql(request.query, load_generated_graph())
    except Exception as exc:  # noqa: BLE001 - preserve SPARQL parse/runtime feedback for demo.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/risk-summary")
def get_risk_summary() -> dict:
    return risk_summary(load_generated_graph())


@app.get("/graph-data")
def get_graph_data() -> dict:
    return graph_data(load_generated_graph())


async def _resolve_csv(file: UploadFile | None) -> Path:
    if file is None:
        return SAMPLE_CSV_PATH

    upload_path = DATA_DIR / "uploaded_transactions.csv"
    content = await file.read()
    upload_path.write_bytes(content)
    return upload_path

