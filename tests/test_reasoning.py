from rdflib import Literal
from rdflib.namespace import RDF, XSD

from backend.services.graph_service import risk_summary
from backend.services.ontology_service import OC, SAMPLE_CSV_PATH, resource
from backend.services.rdf_builder import build_graph_from_csv
from backend.services.reasoning_service import apply_reasoning


def test_reasoning_classifies_wallet_transaction_and_contract_risks():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    assert (resource("wallet", "0xAlice"), RDF.type, OC.HighRiskWallet) in graph
    assert (resource("wallet", "0xBob"), RDF.type, OC.HighRiskWallet) in graph
    assert (resource("tx", "0xTX002"), RDF.type, OC.SuspiciousTransaction) in graph
    assert (resource("contract", "0xRiskyContract"), RDF.type, OC.SuspiciousContract) in graph
    assert (resource("wallet", "0xBob"), OC.hasRiskIndicator, OC.MultipleRiskyRecipientsIndicator) in graph


def test_high_value_transaction_reasoning_classifies_suspicious_transaction():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    tx = resource("tx", "0xTX002")
    assert (tx, RDF.type, OC.SuspiciousTransaction) in graph
    assert (tx, OC.hasRiskIndicator, OC.HighValueTransferIndicator) in graph


def test_mixer_wallet_reasoning_classifies_interacting_wallet():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    alice = resource("wallet", "0xAlice")
    assert (resource("wallet", "0xMixerOne"), RDF.type, OC.MixerWallet) in graph
    assert (alice, RDF.type, OC.HighRiskWallet) in graph
    assert (alice, OC.hasRiskIndicator, OC.MixerInteractionIndicator) in graph


def test_repeated_risky_wallet_interaction_reasoning_classifies_sender():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    bob = resource("wallet", "0xBob")
    assert (bob, RDF.type, OC.HighRiskWallet) in graph
    assert (bob, OC.hasRiskIndicator, OC.MultipleRiskyRecipientsIndicator) in graph


def test_suspicious_contract_reasoning_classifies_contract_with_repeated_high_value_activity():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    contract = resource("contract", "0xRiskyContract")
    assert (contract, RDF.type, OC.SuspiciousContract) in graph
    assert (contract, OC.hasRiskIndicator, OC.SuspiciousContractIndicator) in graph


def test_reasoning_stores_rule_explanations_as_rdf_literals():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    assert (
        resource("wallet", "0xAlice"),
        OC.riskExplanation,
        Literal("Wallet classified as HighRiskWallet because it interacted with a MixerWallet.", datatype=XSD.string),
    ) in graph
    assert (
        resource("tx", "0xTX002"),
        OC.riskExplanation,
        Literal("Transaction classified as SuspiciousTransaction because amount is greater than 10000.", datatype=XSD.string),
    ) in graph
    assert (
        resource("wallet", "0xBob"),
        OC.riskExplanation,
        Literal(
            "Wallet classified as HighRiskWallet because it sent transactions to three or more risky wallets.",
            datatype=XSD.string,
        ),
    ) in graph
    assert (
        resource("contract", "0xRiskyContract"),
        OC.riskExplanation,
        Literal(
            "SmartContract classified as SuspiciousContract because it received repeated high-value transactions.",
            datatype=XSD.string,
        ),
    ) in graph


def test_risk_summary_includes_explanations():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    summary = risk_summary(graph)
    bob = next(row for row in summary["high_risk_wallets"] if row["label"] == "0xBob")
    assert bob["riskScore"] == 95
    assert "Wallet classified as HighRiskWallet because it sent transactions to three or more risky wallets." in bob["explanations"]
