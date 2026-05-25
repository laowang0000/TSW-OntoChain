from backend import main
from backend.services.ontology_service import SAMPLE_CSV_PATH
from backend.services.rdf_builder import build_graph_from_csv
from backend.services.reasoning_service import apply_reasoning


def _reasoned_sample_graph():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)
    return graph


def test_graph_data_endpoint_format(monkeypatch):
    monkeypatch.setattr(main, "load_generated_graph", _reasoned_sample_graph)

    payload = main.get_graph_data()

    assert set(payload) == {"filter", "nodes", "edges"}
    assert payload["filter"] == "all"
    assert payload["nodes"]
    assert payload["edges"]
    first_node = payload["nodes"][0]
    first_edge = payload["edges"][0]
    assert {"id", "label", "type"}.issubset(first_node)
    assert {"from", "to", "label"}.issubset(first_edge)


def test_risk_summary_endpoint_format(monkeypatch):
    monkeypatch.setattr(main, "load_generated_graph", _reasoned_sample_graph)

    payload = main.get_risk_summary()

    expected_keys = {
        "triple_count",
        "wallet_count",
        "transaction_count",
        "smart_contract_count",
        "high_risk_wallet_count",
        "suspicious_transaction_count",
        "suspicious_contract_count",
        "high_risk_wallets",
        "suspicious_transactions",
        "suspicious_contracts",
    }
    assert expected_keys.issubset(payload)
    assert payload["high_risk_wallet_count"] >= 2
    assert payload["suspicious_transaction_count"] >= 3
    wallet_row = payload["high_risk_wallets"][0]
    assert {"id", "label", "riskScore", "indicators", "patterns", "explanations"}.issubset(wallet_row)


def test_graph_data_filter_limits_wallet_transfer_edges(monkeypatch):
    monkeypatch.setattr(main, "load_generated_graph", _reasoned_sample_graph)

    payload = main.get_graph_data(filter_mode="wallet_transfers")

    assert payload["filter"] == "wallet_transfers"
    assert payload["edges"]
    assert {edge["label"] for edge in payload["edges"]}.issubset({"sentTo", "receivedFrom"})


def test_inferred_facts_endpoint_format(monkeypatch):
    monkeypatch.setattr(main, "load_generated_graph", _reasoned_sample_graph)

    payload = main.get_inferred_facts()

    assert payload["inferred_fact_count"] > 0
    first_fact = payload["facts"][0]
    assert {"entity", "entityLabel", "predicate", "object", "triple"}.issubset(first_fact)
    assert any(fact["predicate"] == "rdf:type" for fact in payload["facts"])


def test_risk_evidence_endpoint_includes_source_and_inferred_triples(monkeypatch):
    monkeypatch.setattr(main, "load_generated_graph", _reasoned_sample_graph)

    payload = main.get_risk_evidence("0xAlice")

    assert payload["found"] is True
    assert payload["label"] == "0xAlice"
    assert payload["matchedRules"]
    assert payload["sourceTriples"]
    assert payload["inferredTriples"]
    assert "SELECT ?predicate ?object" in payload["sparqlEvidenceQuery"]
