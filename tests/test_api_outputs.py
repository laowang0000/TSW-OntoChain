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

    assert set(payload) == {"nodes", "edges"}
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
