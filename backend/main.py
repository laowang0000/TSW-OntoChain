"""FastAPI application for the OntoChain semantic risk analysis MVP."""

from __future__ import annotations

from pathlib import Path
from io import StringIO
from typing import Annotated
import csv

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .services.graph_service import graph_data, inferred_facts, risk_evidence, risk_summary
from .services.ontology_service import DATA_DIR, GENERATED_GRAPH_PATH, SAMPLE_CSV_PATH, load_generated_graph, save_graph
from .services.rdf_builder import build_graph_from_csv, triples_as_strings
from .services.reasoning_service import apply_reasoning
from .services.sparql_service import execute_sparql
from .services.validation_service import validate_transaction_csv


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
        "message": "Use POST /build-graph, POST /validate-csv, GET /triples, GET /inferred-facts, POST /query-sparql, GET /risk-summary, GET /risk-evidence, and GET /graph-data.",
    }


@app.post("/validate-csv")
async def validate_csv(file: Annotated[UploadFile | None, File(description="Optional transaction CSV")] = None) -> dict:
    """Validate a transaction CSV before RDF graph construction."""

    try:
        csv_path = await _resolve_csv(file, target_name="uploaded_validation.csv")
        return validate_transaction_csv(csv_path)
    except Exception as exc:  # noqa: BLE001 - API should return a readable demo error.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/build-graph")
async def build_graph(file: Annotated[UploadFile | None, File(description="Optional transaction CSV")] = None) -> dict:
    """Build an RDF graph from an uploaded CSV or the bundled sample CSV."""

    try:
        csv_path = await _resolve_csv(file)
        validation = validate_transaction_csv(csv_path)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={"message": "CSV validation failed.", "validation": validation})
        graph = build_graph_from_csv(csv_path)
        apply_reasoning(graph)
        save_graph(graph, GENERATED_GRAPH_PATH)
        return {"status": "built", "source_csv": str(csv_path), "validation": validation, "summary": risk_summary(graph)}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - API should return a readable demo error.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/triples")
def triples(limit: int = 200) -> dict[str, object]:
    graph = load_generated_graph()
    return {"triple_count": len(graph), "triples": triples_as_strings(graph, limit=limit)}


@app.get("/rdf-turtle")
def rdf_turtle() -> Response:
    """Export the current generated knowledge graph as Turtle."""

    content = load_generated_graph().serialize(format="turtle")
    return Response(content=content, media_type="text/turtle")


@app.get("/inferred-facts")
def get_inferred_facts() -> dict:
    return inferred_facts(load_generated_graph())


@app.post("/query-sparql")
def query_sparql(request: SparqlRequest) -> dict:
    try:
        return execute_sparql(request.query, load_generated_graph())
    except Exception as exc:  # noqa: BLE001 - preserve SPARQL parse/runtime feedback for demo.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/risk-summary")
def get_risk_summary() -> dict:
    return risk_summary(load_generated_graph())


@app.get("/risk-summary.csv")
def get_risk_summary_csv() -> Response:
    """Export the risk summary rows as CSV for report evidence."""

    summary = risk_summary(load_generated_graph())
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["category", "label", "riskScore", "explanations", "indicators", "patterns"])
    writer.writeheader()
    for category, key in (
        ("High-risk wallet", "high_risk_wallets"),
        ("Suspicious transaction", "suspicious_transactions"),
        ("Suspicious contract", "suspicious_contracts"),
    ):
        for row in summary.get(key, []):
            writer.writerow(
                {
                    "category": category,
                    "label": row.get("label", ""),
                    "riskScore": row.get("riskScore", ""),
                    "explanations": " | ".join(row.get("explanations", [])),
                    "indicators": " | ".join(row.get("indicators", [])),
                    "patterns": " | ".join(row.get("patterns", [])),
                }
            )
    return Response(content=output.getvalue(), media_type="text/csv")


@app.get("/risk-evidence")
def get_risk_evidence(entity_id: str) -> dict:
    payload = risk_evidence(load_generated_graph(), entity_id)
    if not payload.get("found"):
        raise HTTPException(status_code=404, detail=payload["message"])
    return payload


@app.get("/graph-data")
def get_graph_data(filter_mode: str = "all") -> dict:
    return graph_data(load_generated_graph(), filter_mode=filter_mode)


async def _resolve_csv(file: UploadFile | None, target_name: str = "uploaded_transactions.csv") -> Path:
    if file is None:
        return SAMPLE_CSV_PATH

    upload_path = DATA_DIR / target_name
    content = await file.read()
    upload_path.write_bytes(content)
    return upload_path
