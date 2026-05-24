from rdflib import Literal
from rdflib.namespace import RDF, XSD

from backend.services.ontology_service import OC, SAMPLE_CSV_PATH, resource
from backend.services.rdf_builder import build_graph_from_csv


def test_rdf_builder_creates_core_semantic_entities():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)

    assert (None, RDF.type, OC.Transaction) in graph
    assert (None, RDF.type, OC.Wallet) in graph
    assert (None, RDF.type, OC.Token) in graph
    assert (None, RDF.type, OC.SmartContract) in graph
    assert (None, OC.sentTo, None) in graph
    assert (None, OC.interactsWithContract, None) in graph
    assert (None, RDF.type, OC.MixerWallet) in graph


def test_csv_to_rdf_conversion_preserves_transaction_fields(tmp_path):
    csv_path = tmp_path / "single_transaction.csv"
    csv_path.write_text(
        "\n".join(
            [
                "tx_hash,sender,receiver,token,amount,timestamp,contract_address,transaction_type",
                "0xTEMP001,0xSender,0xReceiver,USDC,123.45,2026-05-10T09:00:00,0xContract,transfer",
            ]
        ),
        encoding="utf-8",
    )

    graph = build_graph_from_csv(csv_path)
    tx = resource("tx", "0xTEMP001")
    sender = resource("wallet", "0xSender")
    receiver = resource("wallet", "0xReceiver")

    assert (tx, RDF.type, OC.Transaction) in graph
    assert (tx, OC.transactionHash, Literal("0xTEMP001", datatype=XSD.string)) in graph
    assert (tx, OC.amount, Literal("123.45", datatype=XSD.decimal)) in graph
    assert (sender, OC.sentTo, receiver) in graph
    assert (receiver, OC.receivedFrom, sender) in graph
    assert (sender, OC.transactionCount, Literal(1, datatype=XSD.integer)) in graph
