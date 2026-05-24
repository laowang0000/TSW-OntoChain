from backend.services.ontology_service import SAMPLE_CSV_PATH
from backend.services.rdf_builder import build_graph_from_csv
from backend.services.reasoning_service import apply_reasoning
from backend.services.sparql_service import execute_sparql


def test_sparql_returns_inferred_high_risk_wallets():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT ?wallet ?label
        WHERE {
          ?wallet a oc:HighRiskWallet ;
                  rdfs:label ?label .
        }
        ORDER BY ?label
        """,
        graph,
    )

    labels = {row["label"].strip('"') for row in result["rows"]}
    assert {"0xAlice", "0xBob"}.issubset(labels)


def test_sparql_can_query_risk_explanations():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT ?tx ?explanation
        WHERE {
          ?tx a oc:SuspiciousTransaction ;
              oc:transactionHash ?hash ;
              oc:riskExplanation ?explanation .
          FILTER(STR(?hash) = "0xTX002")
        }
        """,
        graph,
    )

    explanations = {row["explanation"].strip('"') for row in result["rows"]}
    assert "Transaction classified as SuspiciousTransaction because amount is greater than 10000." in explanations


def test_sparql_returns_suspicious_transactions():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT ?hash ?amount ?explanation
        WHERE {
          ?tx a oc:SuspiciousTransaction ;
              oc:transactionHash ?hash ;
              oc:amount ?amount ;
              oc:riskExplanation ?explanation .
        }
        ORDER BY DESC(?amount)
        """,
        graph,
    )

    hashes = {row["hash"] for row in result["rows"]}
    assert {"0xTX002", "0xTX003", "0xTX004"}.issubset(hashes)
    assert all("greater than 10000" in row["explanation"] for row in result["rows"])


def test_sparql_returns_wallet_transfer_relationships():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT DISTINCT ?senderLabel ?receiverLabel
        WHERE {
          ?sender oc:sentTo ?receiver ;
                  rdfs:label ?senderLabel .
          ?receiver rdfs:label ?receiverLabel .
        }
        ORDER BY ?senderLabel ?receiverLabel
        """,
        graph,
    )

    transfers = {(row["senderLabel"], row["receiverLabel"]) for row in result["rows"]}
    assert ("0xAlice", "0xMixerOne") in transfers
    assert ("0xBob", "0xMixerThree") in transfers


def test_sparql_returns_smart_contract_interactions():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT DISTINCT ?hash ?amount ?contractLabel
        WHERE {
          ?tx a oc:Transaction ;
              oc:transactionHash ?hash ;
              oc:amount ?amount ;
              oc:interactsWithContract ?contract .
          ?contract rdfs:label ?contractLabel .
        }
        ORDER BY ?contractLabel DESC(?amount)
        """,
        graph,
    )

    interactions = {(row["hash"], row["contractLabel"]) for row in result["rows"]}
    assert ("0xTX002", "0xRiskyContract") in interactions
    assert ("0xTX008", "0xExchangeGateway") in interactions


def test_sparql_returns_all_inferred_facts():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT DISTINCT ?entityLabel ?inferredClass ?predicate ?object
        WHERE {
          VALUES ?inferredClass { oc:HighRiskWallet oc:SuspiciousTransaction oc:SuspiciousContract }
          VALUES ?predicate { oc:riskScore oc:riskExplanation oc:hasRiskIndicator oc:classifiedAs }
          ?entity a ?inferredClass ;
                  rdfs:label ?entityLabel .
          ?entity ?predicate ?object .
        }
        ORDER BY ?inferredClass ?entityLabel ?predicate
        """,
        graph,
    )

    assert result["row_count"] >= 10
    assert any(row["entityLabel"] == "0xBob" and row["predicate"] == "oc:riskExplanation" for row in result["rows"])
    assert any(row["inferredClass"] == "oc:SuspiciousTransaction" for row in result["rows"])


def test_sparql_returns_ontology_classes_used_in_generated_graph():
    graph = build_graph_from_csv(SAMPLE_CSV_PATH)
    apply_reasoning(graph)

    result = execute_sparql(
        """
        SELECT DISTINCT ?class ?classLabel (COUNT(DISTINCT ?entity) AS ?entityCount)
        WHERE {
          ?entity a ?class .
          ?class a owl:Class .
          OPTIONAL { ?class rdfs:label ?classLabel . }
        }
        GROUP BY ?class ?classLabel
        ORDER BY ?class
        """,
        graph,
    )

    classes = {row["class"] for row in result["rows"]}
    assert "oc:Wallet" in classes
    assert "oc:Transaction" in classes
    assert "oc:HighRiskWallet" in classes
    assert "oc:SuspiciousTransaction" in classes
