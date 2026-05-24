"""Graph visualisation and risk summary helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS

from .ontology_service import OC


INSTANCE_CLASSES = {
    OC.Wallet,
    OC.Transaction,
    OC.Token,
    OC.SmartContract,
    OC.ExchangeWallet,
    OC.MixerWallet,
    OC.HighRiskWallet,
    OC.SuspiciousTransaction,
    OC.SuspiciousContract,
    OC.RiskIndicator,
    OC.FraudPattern,
}

EDGE_PROPERTIES = {
    OC.sentTo: "sentTo",
    OC.receivedFrom: "receivedFrom",
    OC.involvesWallet: "involvesWallet",
    OC.interactsWithContract: "interactsWithContract",
    OC.usesToken: "usesToken",
    OC.hasRiskIndicator: "hasRiskIndicator",
    OC.classifiedAs: "classifiedAs",
}


def risk_summary(graph: Graph) -> dict[str, Any]:
    """Build a compact summary of original and inferred risk facts."""

    return {
        "triple_count": len(graph),
        "wallet_count": _count_subjects(graph, OC.Wallet),
        "transaction_count": _count_subjects(graph, OC.Transaction),
        "smart_contract_count": _count_subjects(graph, OC.SmartContract),
        "high_risk_wallet_count": _count_subjects(graph, OC.HighRiskWallet),
        "suspicious_transaction_count": _count_subjects(graph, OC.SuspiciousTransaction),
        "suspicious_contract_count": _count_subjects(graph, OC.SuspiciousContract),
        "high_risk_wallets": _entity_rows(graph, OC.HighRiskWallet),
        "suspicious_transactions": _entity_rows(graph, OC.SuspiciousTransaction),
        "suspicious_contracts": _entity_rows(graph, OC.SuspiciousContract),
    }


def graph_data(graph: Graph) -> dict[str, list[dict[str, Any]]]:
    """Return nodes and edges in a pyvis/networkx-friendly format."""

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for subject in _instance_subjects(graph):
        nodes[str(subject)] = {
            "id": str(subject),
            "label": _label(graph, subject),
            "type": _primary_type(graph, subject),
            "riskScore": _literal_value(graph.value(subject, OC.riskScore)),
            "riskExplanation": "; ".join(sorted(set(str(value) for value in graph.objects(subject, OC.riskExplanation)))),
        }

    for predicate, label in EDGE_PROPERTIES.items():
        for source, _, target in graph.triples((None, predicate, None)):
            if not isinstance(source, URIRef) or not isinstance(target, URIRef):
                continue
            nodes.setdefault(str(source), {"id": str(source), "label": _label(graph, source), "type": _primary_type(graph, source)})
            nodes.setdefault(str(target), {"id": str(target), "label": _label(graph, target), "type": _primary_type(graph, target)})
            edges.append({"from": str(source), "to": str(target), "label": label})

    return {"nodes": list(nodes.values()), "edges": edges}


def _count_subjects(graph: Graph, rdf_class: URIRef) -> int:
    return len(set(graph.subjects(RDF.type, rdf_class)))


def _entity_rows(graph: Graph, rdf_class: URIRef) -> list[dict[str, Any]]:
    rows = []
    for entity in sorted(set(graph.subjects(RDF.type, rdf_class)), key=str):
        indicators = [_label(graph, indicator) for indicator in graph.objects(entity, OC.hasRiskIndicator)]
        patterns = [_label(graph, pattern) for pattern in graph.objects(entity, OC.classifiedAs)]
        explanations = [str(explanation) for explanation in graph.objects(entity, OC.riskExplanation)]
        rows.append(
            {
                "id": str(entity),
                "label": _label(graph, entity),
                "riskScore": _max_literal_value(graph.objects(entity, OC.riskScore)),
                "indicators": sorted(set(indicators)),
                "patterns": sorted(set(patterns)),
                "explanations": sorted(set(explanations)),
            }
        )
    return rows


def _instance_subjects(graph: Graph) -> set[URIRef]:
    subjects: set[URIRef] = set()
    for rdf_class in INSTANCE_CLASSES:
        subjects.update(subject for subject in graph.subjects(RDF.type, rdf_class) if isinstance(subject, URIRef))
    return subjects


def _primary_type(graph: Graph, entity: URIRef) -> str:
    priority = [
        OC.HighRiskWallet,
        OC.MixerWallet,
        OC.ExchangeWallet,
        OC.SuspiciousTransaction,
        OC.SuspiciousContract,
        OC.Transaction,
        OC.SmartContract,
        OC.Wallet,
        OC.Token,
        OC.RiskIndicator,
        OC.FraudPattern,
    ]
    types = set(graph.objects(entity, RDF.type))
    for rdf_class in priority:
        if rdf_class in types:
            return rdf_class.split("#")[-1]
    return "Resource"


def _label(graph: Graph, entity: URIRef) -> str:
    label = graph.value(entity, RDFS.label)
    if label:
        return str(label)
    return entity.split("#")[-1]


def _literal_value(value: Any) -> Any:
    if value is None:
        return None
    return value.toPython() if hasattr(value, "toPython") else str(value)


def _max_literal_value(values: Any) -> Any:
    python_values = [_literal_value(value) for value in values]
    numeric_values = [value for value in python_values if isinstance(value, int)]
    if numeric_values:
        return max(numeric_values)
    return python_values[0] if python_values else None
