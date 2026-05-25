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

INFERRED_CLASSES = {
    OC.HighRiskWallet,
    OC.SuspiciousTransaction,
    OC.SuspiciousContract,
}

INFERRED_PROPERTIES = {
    RDF.type,
    OC.hasRiskIndicator,
    OC.classifiedAs,
    OC.riskScore,
    OC.riskExplanation,
}

GRAPH_FILTERS = {
    "all": set(EDGE_PROPERTIES),
    "risk_entities": {OC.hasRiskIndicator, OC.classifiedAs},
    "wallet_transfers": {OC.sentTo, OC.receivedFrom},
    "contract_interactions": {OC.interactsWithContract},
    "inferred_relationships": {OC.hasRiskIndicator, OC.classifiedAs},
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


def graph_data(graph: Graph, filter_mode: str = "all") -> dict[str, Any]:
    """Return nodes and edges in a pyvis/networkx-friendly format."""

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    allowed_predicates = GRAPH_FILTERS.get(filter_mode, GRAPH_FILTERS["all"])

    for subject in _subjects_for_filter(graph, filter_mode):
        nodes[str(subject)] = {
            "id": str(subject),
            "label": _label(graph, subject),
            "type": _primary_type(graph, subject),
            "riskScore": _literal_value(graph.value(subject, OC.riskScore)),
            "riskExplanation": "; ".join(sorted(set(str(value) for value in graph.objects(subject, OC.riskExplanation)))),
        }

    for predicate, label in EDGE_PROPERTIES.items():
        if predicate not in allowed_predicates:
            continue
        for source, _, target in graph.triples((None, predicate, None)):
            if not isinstance(source, URIRef) or not isinstance(target, URIRef):
                continue
            nodes.setdefault(str(source), {"id": str(source), "label": _label(graph, source), "type": _primary_type(graph, source)})
            nodes.setdefault(str(target), {"id": str(target), "label": _label(graph, target), "type": _primary_type(graph, target)})
            edges.append({"from": str(source), "to": str(target), "label": label})

    return {"filter": filter_mode if filter_mode in GRAPH_FILTERS else "all", "nodes": list(nodes.values()), "edges": edges}


def inferred_facts(graph: Graph) -> dict[str, Any]:
    """Return the RDF facts that make inferred risk classifications visible."""

    triples = []
    for entity in sorted(_inferred_entities(graph), key=str):
        for subject, predicate, obj in graph.triples((entity, None, None)):
            if predicate == RDF.type and obj not in INFERRED_CLASSES:
                continue
            if predicate not in INFERRED_PROPERTIES:
                continue
            triples.append(
                {
                    "entity": str(subject),
                    "entityLabel": _label(graph, subject),
                    "predicate": predicate.n3(graph.namespace_manager),
                    "object": _term_to_string(graph, obj),
                    "triple": _triple_to_string(graph, subject, predicate, obj),
                }
            )
    return {"inferred_fact_count": len(triples), "facts": triples}


def risk_evidence(graph: Graph, entity_id: str) -> dict[str, Any]:
    """Build an evidence view for one inferred wallet, transaction, or contract."""

    entity = _resolve_entity(graph, entity_id)
    if entity is None:
        return {"found": False, "entity_id": entity_id, "message": "No matching RDF resource found."}

    inferred_triples = _inferred_triples_for_entity(graph, entity)
    source_triples = _source_triples_for_entity(graph, entity)
    explanations = sorted(set(str(value) for value in graph.objects(entity, OC.riskExplanation)))

    return {
        "found": True,
        "entity": str(entity),
        "label": _label(graph, entity),
        "type": _primary_type(graph, entity),
        "riskScore": _max_literal_value(graph.objects(entity, OC.riskScore)),
        "matchedRules": _matched_rule_rows(graph, entity),
        "explanations": explanations,
        "sourceTriples": [_triple_to_string(graph, *triple) for triple in source_triples],
        "inferredTriples": [_triple_to_string(graph, *triple) for triple in inferred_triples],
        "sparqlEvidenceQuery": _evidence_query(entity),
    }


def _count_subjects(graph: Graph, rdf_class: URIRef) -> int:
    return len(set(graph.subjects(RDF.type, rdf_class)))


def _subjects_for_filter(graph: Graph, filter_mode: str) -> set[URIRef]:
    if filter_mode == "risk_entities" or filter_mode == "inferred_relationships":
        subjects = _inferred_entities(graph)
        for entity in list(subjects):
            subjects.update(obj for obj in graph.objects(entity, OC.hasRiskIndicator) if isinstance(obj, URIRef))
            subjects.update(obj for obj in graph.objects(entity, OC.classifiedAs) if isinstance(obj, URIRef))
        return subjects
    if filter_mode == "wallet_transfers":
        subjects = set()
        for source, _, target in graph.triples((None, OC.sentTo, None)):
            if isinstance(source, URIRef):
                subjects.add(source)
            if isinstance(target, URIRef):
                subjects.add(target)
        return subjects
    if filter_mode == "contract_interactions":
        subjects = set()
        for transaction, _, contract in graph.triples((None, OC.interactsWithContract, None)):
            if isinstance(transaction, URIRef):
                subjects.add(transaction)
            if isinstance(contract, URIRef):
                subjects.add(contract)
        return subjects
    return _instance_subjects(graph)


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


def _inferred_entities(graph: Graph) -> set[URIRef]:
    subjects: set[URIRef] = set()
    for rdf_class in INFERRED_CLASSES:
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


def _resolve_entity(graph: Graph, entity_id: str) -> URIRef | None:
    if entity_id.startswith("http://") or entity_id.startswith("https://"):
        candidate = URIRef(entity_id)
        return candidate if (candidate, None, None) in graph else None
    for subject in _instance_subjects(graph):
        if str(subject) == entity_id or _label(graph, subject) == entity_id:
            return subject
    return None


def _matched_rule_rows(graph: Graph, entity: URIRef) -> list[dict[str, Any]]:
    rows = []
    indicators = sorted(set(_label(graph, indicator) for indicator in graph.objects(entity, OC.hasRiskIndicator)))
    patterns = sorted(set(_label(graph, pattern) for pattern in graph.objects(entity, OC.classifiedAs)))
    explanations = sorted(set(str(value) for value in graph.objects(entity, OC.riskExplanation)))
    for index, explanation in enumerate(explanations, start=1):
        rows.append(
            {
                "ruleId": f"R{index}",
                "indicator": indicators[index - 1] if index - 1 < len(indicators) else "",
                "fraudPattern": patterns[index - 1] if index - 1 < len(patterns) else "",
                "explanation": explanation,
            }
        )
    return rows


def _source_triples_for_entity(graph: Graph, entity: URIRef) -> list[tuple[Any, Any, Any]]:
    triples: set[tuple[Any, Any, Any]] = set()
    source_predicates = {
        OC.sentTo,
        OC.receivedFrom,
        OC.involvesWallet,
        OC.interactsWithContract,
        OC.usesToken,
        OC.amount,
        OC.timestamp,
        OC.transactionHash,
        OC.transactionType,
        OC.walletAddress,
        OC.transactionCount,
    }
    for predicate in source_predicates:
        triples.update(graph.triples((entity, predicate, None)))
        triples.update(graph.triples((None, predicate, entity)))

    for transaction in graph.subjects(OC.involvesWallet, entity):
        triples.update(graph.triples((transaction, OC.transactionHash, None)))
        triples.update(graph.triples((transaction, OC.amount, None)))
        triples.update(graph.triples((transaction, OC.interactsWithContract, None)))

    for transaction in graph.subjects(OC.interactsWithContract, entity):
        triples.update(graph.triples((transaction, OC.transactionHash, None)))
        triples.update(graph.triples((transaction, OC.amount, None)))
        triples.update(graph.triples((transaction, OC.interactsWithContract, entity)))

    return sorted(triples, key=lambda triple: tuple(str(part) for part in triple))


def _inferred_triples_for_entity(graph: Graph, entity: URIRef) -> list[tuple[Any, Any, Any]]:
    triples: set[tuple[Any, Any, Any]] = set()
    for predicate in INFERRED_PROPERTIES:
        for triple in graph.triples((entity, predicate, None)):
            if predicate == RDF.type and triple[2] not in INFERRED_CLASSES:
                continue
            triples.add(triple)
    return sorted(triples, key=lambda triple: tuple(str(part) for part in triple))


def _evidence_query(entity: URIRef) -> str:
    return f"""SELECT ?predicate ?object
WHERE {{
  <{entity}> ?predicate ?object .
  VALUES ?predicate {{ rdf:type oc:riskScore oc:riskExplanation oc:hasRiskIndicator oc:classifiedAs }}
}}
ORDER BY ?predicate ?object"""


def _term_to_string(graph: Graph, term: Any) -> str:
    if hasattr(term, "n3"):
        return term.n3(graph.namespace_manager)
    return str(term)


def _triple_to_string(graph: Graph, subject: Any, predicate: Any, obj: Any) -> str:
    return f"{_term_to_string(graph, subject)} {_term_to_string(graph, predicate)} {_term_to_string(graph, obj)}"
