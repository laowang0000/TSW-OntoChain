"""Rule-based inference for wallet, transaction, and contract risk.

The rules are deliberately explicit because the project assessment values
clarity. Each rule adds RDF facts back into the graph, which means inferred
knowledge can be queried with SPARQL and visualised like original CSV facts.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from .ontology_service import OC


HIGH_VALUE_THRESHOLD = Decimal("10000")
RISKY_RECIPIENT_THRESHOLD = 3
CONTRACT_HIGH_VALUE_THRESHOLD = 3


def apply_reasoning(graph: Graph) -> Graph:
    """Apply the OntoChain risk rules and return the enriched graph."""

    _rule_wallet_interacts_with_mixer(graph)
    _rule_high_value_transactions(graph)
    _rule_wallet_sends_to_many_risky_wallets(graph)
    _rule_contract_receives_many_high_value_transactions(graph)
    return graph


def _classify(
    graph: Graph,
    entity: URIRef,
    rdf_class: URIRef,
    indicator: URIRef,
    pattern: URIRef,
    score: int,
    explanation: str,
) -> None:
    graph.add((entity, RDF.type, rdf_class))
    graph.add((entity, OC.hasRiskIndicator, indicator))
    graph.add((entity, OC.classifiedAs, pattern))
    graph.add((entity, OC.riskScore, Literal(score, datatype=XSD.integer)))
    graph.add((entity, OC.riskExplanation, Literal(explanation, datatype=XSD.string)))


def _rule_wallet_interacts_with_mixer(graph: Graph) -> None:
    """If a wallet interacts with a MixerWallet, classify it as HighRiskWallet."""

    mixer_wallets = set(graph.subjects(RDF.type, OC.MixerWallet))
    for wallet, _, target in graph.triples((None, OC.sentTo, None)):
        if target in mixer_wallets:
            _classify(
                graph,
                wallet,
                OC.HighRiskWallet,
                OC.MixerInteractionIndicator,
                OC.MixerExposurePattern,
                90,
                "Wallet classified as HighRiskWallet because it interacted with a MixerWallet.",
            )
    for wallet, _, source in graph.triples((None, OC.receivedFrom, None)):
        if source in mixer_wallets:
            _classify(
                graph,
                wallet,
                OC.HighRiskWallet,
                OC.MixerInteractionIndicator,
                OC.MixerExposurePattern,
                90,
                "Wallet classified as HighRiskWallet because it interacted with a MixerWallet.",
            )


def _rule_high_value_transactions(graph: Graph) -> None:
    """If a transaction amount is above 10000, classify it as SuspiciousTransaction."""

    for transaction, _, amount_literal in graph.triples((None, OC.amount, None)):
        try:
            amount = Decimal(str(amount_literal))
        except (InvalidOperation, TypeError):
            continue
        if amount > HIGH_VALUE_THRESHOLD:
            _classify(
                graph,
                transaction,
                OC.SuspiciousTransaction,
                OC.HighValueTransferIndicator,
                OC.LargeTransferPattern,
                80,
                "Transaction classified as SuspiciousTransaction because amount is greater than 10000.",
            )


def _rule_wallet_sends_to_many_risky_wallets(graph: Graph) -> None:
    """If a wallet sends to three or more risky wallets, classify it as HighRiskWallet."""

    risky_wallets = set(graph.subjects(RDF.type, OC.MixerWallet)) | set(graph.subjects(RDF.type, OC.HighRiskWallet))
    recipients_by_wallet: dict[URIRef, set[URIRef]] = defaultdict(set)

    for wallet, _, recipient in graph.triples((None, OC.sentTo, None)):
        if recipient in risky_wallets:
            recipients_by_wallet[wallet].add(recipient)

    for wallet, recipients in recipients_by_wallet.items():
        if len(recipients) >= RISKY_RECIPIENT_THRESHOLD:
            _classify(
                graph,
                wallet,
                OC.HighRiskWallet,
                OC.MultipleRiskyRecipientsIndicator,
                OC.RiskFanOutPattern,
                95,
                "Wallet classified as HighRiskWallet because it sent transactions to three or more risky wallets.",
            )


def _rule_contract_receives_many_high_value_transactions(graph: Graph) -> None:
    """If a smart contract receives many high-value transactions, flag it."""

    high_value_counts: dict[URIRef, int] = defaultdict(int)
    for transaction, _, contract in graph.triples((None, OC.interactsWithContract, None)):
        amount_literal = graph.value(transaction, OC.amount)
        if amount_literal is None:
            continue
        try:
            amount = Decimal(str(amount_literal))
        except (InvalidOperation, TypeError):
            continue
        if amount > HIGH_VALUE_THRESHOLD:
            high_value_counts[contract] += 1

    for contract, count in high_value_counts.items():
        if count >= CONTRACT_HIGH_VALUE_THRESHOLD:
            _classify(
                graph,
                contract,
                OC.SuspiciousContract,
                OC.SuspiciousContractIndicator,
                OC.ContractConcentrationPattern,
                85,
                "SmartContract classified as SuspiciousContract because it received repeated high-value transactions.",
            )
