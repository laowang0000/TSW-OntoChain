"""Ontology loading and shared RDF helpers for OntoChain.

The project intentionally keeps ontology handling small and visible: the
ontology is stored as Turtle, loaded into RDFLib, and reused by all services so
that generated transaction data and inferred classifications share one
vocabulary.
"""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import Graph, Namespace, URIRef


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
ONTOLOGY_PATH = DATA_DIR / "ontology.ttl"
GENERATED_GRAPH_PATH = DATA_DIR / "generated_graph.ttl"
SAMPLE_CSV_PATH = DATA_DIR / "sample_transactions.csv"

OC = Namespace("http://example.org/ontochain#")


def bind_namespaces(graph: Graph) -> Graph:
    """Bind common prefixes so Turtle output and SPARQL results are readable."""

    graph.bind("oc", OC)
    graph.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    graph.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    graph.bind("owl", "http://www.w3.org/2002/07/owl#")
    graph.bind("xsd", "http://www.w3.org/2001/XMLSchema#")
    return graph


def load_ontology() -> Graph:
    """Load the OWL/RDFS ontology from Turtle."""

    graph = bind_namespaces(Graph())
    graph.parse(ONTOLOGY_PATH, format="turtle")
    return graph


def create_graph_with_ontology() -> Graph:
    """Create a graph that already contains the ontology triples."""

    return load_ontology()


def load_generated_graph() -> Graph:
    """Load the generated graph if present, otherwise return ontology only."""

    graph = bind_namespaces(Graph())
    if GENERATED_GRAPH_PATH.exists() and GENERATED_GRAPH_PATH.stat().st_size > 0:
        graph.parse(GENERATED_GRAPH_PATH, format="turtle")
        return graph
    return load_ontology()


def save_graph(graph: Graph, path: Path = GENERATED_GRAPH_PATH) -> None:
    """Serialize an RDFLib graph as Turtle."""

    bind_namespaces(graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(path), format="turtle")


def safe_fragment(value: str) -> str:
    """Convert a blockchain value into a URI-safe fragment."""

    cleaned = str(value).strip()
    if not cleaned:
        cleaned = "unknown"
    return re.sub(r"[^A-Za-z0-9_]+", "_", cleaned).strip("_")


def resource(kind: str, value: str) -> URIRef:
    """Build a stable resource URI under the ontology namespace."""

    return OC[f"{kind}_{safe_fragment(value)}"]

