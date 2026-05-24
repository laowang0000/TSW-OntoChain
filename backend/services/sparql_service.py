"""SPARQL query execution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph, Literal

from .ontology_service import GENERATED_GRAPH_PATH, bind_namespaces


DEFAULT_PREFIXES = """PREFIX oc: <http://example.org/ontochain#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


def load_graph_for_query(graph_path: str | Path = GENERATED_GRAPH_PATH) -> Graph:
    graph = bind_namespaces(Graph())
    graph.parse(str(graph_path), format="turtle")
    return graph


def execute_sparql(query: str, graph: Graph | None = None) -> dict[str, Any]:
    """Run a SPARQL SELECT query and return JSON-friendly rows."""

    active_graph = graph or load_graph_for_query()
    prepared_query = _with_default_prefixes(query)
    result = active_graph.query(prepared_query)
    variables = [str(variable) for variable in result.vars]
    rows = []

    for row in result:
        rows.append({variables[index]: _term_to_string(row[index], active_graph) for index in range(len(variables))})

    return {"columns": variables, "rows": rows, "row_count": len(rows)}


def _with_default_prefixes(query: str) -> str:
    lower_query = query.lower()
    if "prefix oc:" in lower_query:
        return query
    return f"{DEFAULT_PREFIXES}\n{query}"


def _term_to_string(term: Any, graph: Graph) -> str:
    if term is None:
        return ""
    if isinstance(term, Literal):
        return str(term)
    try:
        return term.n3(graph.namespace_manager)
    except AttributeError:
        return str(term)
