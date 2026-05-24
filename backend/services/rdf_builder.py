"""Build RDF triples from blockchain transaction CSV data."""

from __future__ import annotations

import csv
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Literal
from rdflib.namespace import RDF, RDFS, XSD

from .ontology_service import OC, create_graph_with_ontology, resource, save_graph


REQUIRED_FIELDS = {
    "tx_hash",
    "sender",
    "receiver",
    "token",
    "amount",
    "timestamp",
    "contract_address",
    "transaction_type",
}


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required field(s): {', '.join(sorted(missing))}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def _decimal_literal(raw_amount: str) -> Literal:
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid transaction amount: {raw_amount}") from exc
    return Literal(amount, datatype=XSD.decimal)


def build_graph_from_csv(csv_path: str | Path, output_path: str | Path | None = None) -> Graph:
    """Convert CSV transaction rows into RDF triples.

    The builder creates explicit domain entities for wallets, transactions,
    tokens, and smart contracts. It also tags known exchange/mixer wallets using
    the transaction_type field so the reasoning stage has initial risk evidence.
    """

    csv_path = Path(csv_path)
    graph = create_graph_with_ontology()
    rows = _read_rows(csv_path)
    outgoing_counts: Counter[str] = Counter()

    for row in rows:
        tx = resource("tx", row["tx_hash"])
        sender = resource("wallet", row["sender"])
        receiver = resource("wallet", row["receiver"])
        token = resource("token", row["token"])
        contract = resource("contract", row["contract_address"])
        transaction_type = row["transaction_type"].lower()

        outgoing_counts[row["sender"]] += 1

        graph.add((tx, RDF.type, OC.Transaction))
        graph.add((tx, RDFS.label, Literal(row["tx_hash"])))
        graph.add((tx, OC.transactionHash, Literal(row["tx_hash"], datatype=XSD.string)))
        graph.add((tx, OC.amount, _decimal_literal(row["amount"])))
        graph.add((tx, OC.timestamp, Literal(row["timestamp"], datatype=XSD.dateTime)))
        graph.add((tx, OC.transactionType, Literal(row["transaction_type"], datatype=XSD.string)))

        for wallet_uri, address in ((sender, row["sender"]), (receiver, row["receiver"])):
            graph.add((wallet_uri, RDF.type, OC.Wallet))
            graph.add((wallet_uri, RDFS.label, Literal(address)))
            graph.add((wallet_uri, OC.walletAddress, Literal(address, datatype=XSD.string)))

        graph.add((token, RDF.type, OC.Token))
        graph.add((token, RDFS.label, Literal(row["token"])))

        graph.add((contract, RDF.type, OC.SmartContract))
        graph.add((contract, RDFS.label, Literal(row["contract_address"])))

        graph.add((sender, OC.sentTo, receiver))
        graph.add((receiver, OC.receivedFrom, sender))
        graph.add((tx, OC.involvesWallet, sender))
        graph.add((tx, OC.involvesWallet, receiver))
        graph.add((tx, OC.usesToken, token))
        graph.add((tx, OC.interactsWithContract, contract))

        if "mixer" in transaction_type:
            mixer_wallet = sender if "withdraw" in transaction_type else receiver
            graph.add((mixer_wallet, RDF.type, OC.MixerWallet))
        if "exchange" in transaction_type:
            graph.add((receiver, RDF.type, OC.ExchangeWallet))

    _add_wallet_transaction_counts(graph, outgoing_counts)

    if output_path is not None:
        save_graph(graph, Path(output_path))

    return graph


def _add_wallet_transaction_counts(graph: Graph, outgoing_counts: Counter[str]) -> None:
    """Attach outgoing transaction counts to wallets for transparent querying."""

    for address, count in outgoing_counts.items():
        graph.add((resource("wallet", address), OC.transactionCount, Literal(count, datatype=XSD.integer)))


def triples_as_strings(graph: Graph, limit: int = 200) -> list[str]:
    """Return readable triples for API and UI display."""

    rows: Iterable[tuple] = graph.triples((None, None, None))
    return [f"{s.n3(graph.namespace_manager)} {p.n3(graph.namespace_manager)} {o.n3(graph.namespace_manager)}" for s, p, o in list(rows)[:limit]]
