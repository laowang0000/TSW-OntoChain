"""Streamlit frontend for the OntoChain semantic risk demo.

The interface is organised around the university presentation flow:
CSV data -> RDF triples -> inferred risk labels -> SPARQL -> graph view.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tempfile
from typing import Any

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

try:
    from pyvis.network import Network
except ModuleNotFoundError:
    Network = None


DEFAULT_API_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV_PATH = PROJECT_ROOT / "backend" / "data" / "sample_transactions.csv"

PREDEFINED_QUERIES = {
    "High-risk wallets with explanations": {
        "question": "Which wallets were inferred as high risk, and which rule explains each classification?",
        "query": """SELECT DISTINCT ?wallet ?label ?score ?explanation
WHERE {
  ?wallet a oc:HighRiskWallet ;
          rdfs:label ?label ;
          oc:riskScore ?score ;
          oc:riskExplanation ?explanation .
}
ORDER BY DESC(?score)""",
    },
    "Suspicious transactions with explanations": {
        "question": "Which transactions were inferred as suspicious, what amount caused the risk, and what rule explains it?",
        "query": """SELECT DISTINCT ?tx ?hash ?amount ?contract ?explanation
WHERE {
  ?tx a oc:SuspiciousTransaction ;
      oc:transactionHash ?hash ;
      oc:amount ?amount ;
      oc:interactsWithContract ?contract ;
      oc:riskExplanation ?explanation .
}
ORDER BY DESC(?amount)""",
    },
    "Wallet-to-wallet transfers": {
        "question": "Which wallet resources are connected by the `oc:sentTo` object property?",
        "query": """SELECT DISTINCT ?sender ?senderLabel ?receiver ?receiverLabel
WHERE {
  ?sender oc:sentTo ?receiver ;
          rdfs:label ?senderLabel .
  ?receiver rdfs:label ?receiverLabel .
}
ORDER BY ?senderLabel ?receiverLabel""",
    },
    "Smart contract interactions": {
        "question": "Which transaction resources interact with which smart contract resources?",
        "query": """SELECT DISTINCT ?tx ?hash ?amount ?contract ?contractLabel
WHERE {
  ?tx a oc:Transaction ;
      oc:transactionHash ?hash ;
      oc:amount ?amount ;
      oc:interactsWithContract ?contract .
  ?contract rdfs:label ?contractLabel .
}
ORDER BY ?contractLabel DESC(?amount)""",
    },
    "All inferred facts": {
        "question": "Which RDF facts were added by reasoning for risk classification and explanation?",
        "query": """SELECT DISTINCT ?entity ?entityLabel ?inferredClass ?predicate ?object
WHERE {
  VALUES ?inferredClass { oc:HighRiskWallet oc:SuspiciousTransaction oc:SuspiciousContract }
  VALUES ?predicate { oc:riskScore oc:riskExplanation oc:hasRiskIndicator oc:classifiedAs }
  ?entity a ?inferredClass ;
          rdfs:label ?entityLabel .
  ?entity ?predicate ?object .
}
ORDER BY ?inferredClass ?entityLabel ?predicate""",
    },
    "Ontology classes used in graph": {
        "question": "Which OWL ontology classes have instances in the generated knowledge graph?",
        "query": """SELECT DISTINCT ?class ?classLabel (COUNT(DISTINCT ?entity) AS ?entityCount)
WHERE {
  ?entity a ?class .
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?classLabel . }
}
GROUP BY ?class ?classLabel
ORDER BY ?class""",
    },
    "Mixer exposure relationships": {
        "question": "Which wallet-to-wallet transfers involve a wallet identified as a mixer?",
        "query": """SELECT DISTINCT ?wallet ?walletLabel ?mixer ?mixerLabel
WHERE {
  ?wallet oc:sentTo ?mixer ;
          rdfs:label ?walletLabel .
  ?mixer a oc:MixerWallet ;
         rdfs:label ?mixerLabel .
}""",
    },
}


def api_get(api_url: str, endpoint: str, **params: Any) -> dict[str, Any] | None:
    """Call a backend GET endpoint and show a friendly Streamlit error."""

    try:
        response = requests.get(f"{api_url}{endpoint}", params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        show_backend_error(exc)
        return None


def api_post(api_url: str, endpoint: str, **kwargs: Any) -> dict[str, Any] | None:
    """Call a backend POST endpoint and show a friendly Streamlit error."""

    try:
        response = requests.post(f"{api_url}{endpoint}", timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        show_backend_error(exc)
        return None


def api_get_text(api_url: str, endpoint: str) -> str | None:
    """Call a text export endpoint and return the response body."""

    try:
        response = requests.get(f"{api_url}{endpoint}", timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        show_backend_error(exc)
        return None


def check_backend(api_url: str) -> bool:
    """Return True when FastAPI is reachable without flooding the UI."""

    try:
        response = requests.get(f"{api_url}/", timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def show_backend_error(exc: requests.RequestException) -> None:
    st.warning(
        "FastAPI backend is not reachable yet. Start it with "
        "`uvicorn backend.main:app --reload`, then click **Build RDF knowledge graph**."
    )
    with st.expander("Technical error details"):
        st.code(str(exc))


def list_to_text(value: Any) -> str:
    """Display list-valued risk explanations in a compact table cell."""

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return "" if value is None else str(value)


def risk_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert risk summary rows into a presentation-friendly table."""

    if not rows:
        return pd.DataFrame(columns=["label", "riskScore", "explanations", "indicators", "patterns"])
    frame = pd.DataFrame(rows)
    for column in ("explanations", "indicators", "patterns"):
        if column in frame:
            frame[column] = frame[column].apply(list_to_text)
    return frame[["label", "riskScore", "explanations", "indicators", "patterns"]]


def query_result_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Create a readable dataframe for SPARQL results."""

    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    for column in frame.columns:
        frame[column] = frame[column].apply(list_to_text)
    return frame


def validation_issue_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Format validation errors or warnings for display."""

    if not rows:
        return pd.DataFrame(columns=["row", "field", "message"])
    return pd.DataFrame(rows)[["row", "field", "message"]]


def inferred_fact_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Format inferred RDF facts for the dedicated inference evidence tab."""

    if not rows:
        return pd.DataFrame(columns=["entityLabel", "predicate", "object", "triple"])
    return pd.DataFrame(rows)[["entityLabel", "predicate", "object", "triple"]]


def risk_entity_options(summary: dict[str, Any]) -> dict[str, str]:
    """Return display labels mapped to RDF resource identifiers for evidence lookup."""

    options: dict[str, str] = {}
    for category, key in (
        ("Wallet", "high_risk_wallets"),
        ("Transaction", "suspicious_transactions"),
        ("Contract", "suspicious_contracts"),
    ):
        for row in summary.get(key, []):
            options[f"{category}: {row.get('label')}"] = row.get("id", "")
    return options


def csv_bytes_from_frame(frame: pd.DataFrame) -> bytes:
    """Convert a dataframe to CSV bytes for Streamlit downloads."""

    return frame.to_csv(index=False).encode("utf-8")


def load_visible_csv(uploaded_file: Any) -> tuple[pd.DataFrame, str]:
    """Load either the uploaded CSV or the bundled sample for the raw-data tab."""

    if uploaded_file is not None:
        return pd.read_csv(BytesIO(uploaded_file.getvalue())), f"Uploaded CSV: {uploaded_file.name}"
    return pd.read_csv(SAMPLE_CSV_PATH), "Bundled sample CSV"


def render_metric_row(summary: dict[str, Any]) -> None:
    metrics = [
        ("Triples", summary.get("triple_count", 0)),
        ("Wallets", summary.get("wallet_count", 0)),
        ("Transactions", summary.get("transaction_count", 0)),
        ("High-risk wallets", summary.get("high_risk_wallet_count", 0)),
        ("Suspicious tx", summary.get("suspicious_transaction_count", 0)),
        ("Suspicious contracts", summary.get("suspicious_contract_count", 0)),
    ]
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def render_graph(data: dict[str, Any]) -> None:
    """Render pyvis graph data from the backend."""

    if Network is None:
        st.error("Knowledge graph visualisation requires `pyvis`, but it is not installed in this Python environment.")
        st.code("python -m pip install pyvis==0.3.2")
        st.info("The RDF triples, inferred risks, SPARQL queries, and summaries still work without pyvis.")
        return

    network = Network(height="650px", width="100%", bgcolor="#ffffff", font_color="#1f2937", directed=True)
    network.barnes_hut(gravity=-22000, central_gravity=0.3, spring_length=150)

    color_by_type = {
        "HighRiskWallet": "#dc2626",
        "MixerWallet": "#f97316",
        "ExchangeWallet": "#2563eb",
        "SuspiciousTransaction": "#be123c",
        "SuspiciousContract": "#7c2d12",
        "Transaction": "#64748b",
        "SmartContract": "#9333ea",
        "Token": "#059669",
        "RiskIndicator": "#ca8a04",
        "FraudPattern": "#0f766e",
    }

    for node in data.get("nodes", []):
        node_type = node.get("type", "Resource")
        explanation = node.get("riskExplanation") or "No risk explanation"
        title = f"{node.get('label')}<br>{node_type}<br>Risk: {node.get('riskScore')}<br>{explanation}"
        network.add_node(node["id"], label=node.get("label"), title=title, color=color_by_type.get(node_type, "#475569"))
    for edge in data.get("edges", []):
        network.add_edge(edge["from"], edge["to"], label=edge["label"], arrows="to")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as handle:
        network.save_graph(handle.name)
        html = Path(handle.name).read_text(encoding="utf-8")
    components.html(html, height=680, scrolling=True)


st.set_page_config(page_title="OntoChain", layout="wide")
st.title("OntoChain Semantic Blockchain Risk System")
st.caption("A guided Semantic Web demo: CSV transactions become RDF triples, OWL/RDFS concepts, inferred risk labels, SPARQL results, and a knowledge graph.")

api_url = st.sidebar.text_input("FastAPI URL", DEFAULT_API_URL).rstrip("/")
uploaded_file = st.sidebar.file_uploader("Upload transaction CSV", type=["csv"])

st.sidebar.markdown("Demo order")
st.sidebar.markdown("1. CSV data\n2. Validation\n3. RDF triples\n4. Inference\n5. Evidence\n6. SPARQL\n7. Graph\n8. Explanation")
st.sidebar.markdown("Required CSV fields")
st.sidebar.code("tx_hash, sender, receiver, token, amount, timestamp, contract_address, transaction_type")

if st.sidebar.button("Validate CSV"):
    files = None
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
    validation_result = api_post(api_url, "/validate-csv", files=files)
    if validation_result:
        st.session_state["validation_result"] = validation_result
        if validation_result.get("valid"):
            st.sidebar.success("CSV validation passed")
        else:
            st.sidebar.error("CSV validation failed")

if st.sidebar.button("Build RDF knowledge graph", type="primary"):
    files = None
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
    result = api_post(api_url, "/build-graph", files=files)
    if result:
        st.session_state["build_result"] = result
        st.session_state["validation_result"] = result.get("validation")
        st.success("Knowledge graph built. RDF triples were generated and reasoning rules were applied.")

backend_online = check_backend(api_url)
if backend_online:
    st.sidebar.success("FastAPI connected")
else:
    st.sidebar.error("FastAPI offline")
    st.warning(
        "FastAPI backend is not reachable yet. Start it with "
        "`uvicorn backend.main:app --reload`, then return to this page."
    )

tab_csv, tab_validation, tab_rdf, tab_inference, tab_evidence, tab_sparql, tab_graph, tab_explain = st.tabs(
    [
        "1. Raw CSV",
        "2. Validation",
        "3. RDF triples",
        "4. Inferred facts",
        "5. Risk evidence",
        "6. SPARQL",
        "7. Knowledge graph",
        "8. Semantic Web use",
    ]
)

with tab_csv:
    st.header("1. Raw CSV transaction data")
    st.write(
        "This is the source data before Semantic Web processing. Each row is converted into RDF resources for wallets, "
        "transactions, tokens, and smart contracts."
    )
    try:
        csv_frame, csv_label = load_visible_csv(uploaded_file)
        st.caption(csv_label)
        st.dataframe(csv_frame, use_container_width=True)
        st.info("Presentation point: this table is ordinary tabular data. The next tab shows how it becomes machine-readable RDF.")
    except Exception as exc:  # noqa: BLE001 - Streamlit should keep the demo alive on malformed uploads.
        st.error(f"Could not read the CSV file: {exc}")

with tab_validation:
    st.header("2. Semantic validation before RDF generation")
    st.write(
        "This step checks whether the tabular data can be safely transformed into ontology-aligned RDF resources. "
        "It supports data quality before graph construction."
    )
    validation = st.session_state.get("validation_result")
    if validation is None:
        st.info("Click **Validate CSV** or **Build RDF knowledge graph** in the sidebar to generate a validation report.")
    else:
        if validation.get("valid"):
            st.success(f"Validation passed. {validation.get('row_count', 0)} transaction rows checked.")
        else:
            st.error("Validation failed. Fix the listed errors before RDF generation.")
        st.caption("Required ontology-mapped CSV fields")
        st.code(", ".join(validation.get("required_fields", [])))
        st.subheader("Errors")
        st.dataframe(validation_issue_dataframe(validation.get("errors", [])), use_container_width=True)
        st.subheader("Warnings")
        st.dataframe(validation_issue_dataframe(validation.get("warnings", [])), use_container_width=True)

with tab_rdf:
    st.header("3. RDF triples generated from the CSV")
    st.write(
        "RDF expresses the blockchain data as subject-predicate-object triples. "
        "Examples include wallet-to-wallet transfers, transaction amounts, token usage, and contract interactions."
    )
    triples = api_get(api_url, "/triples", limit=120) if backend_online else None
    if triples:
        st.write(f"Showing up to 120 of {triples['triple_count']} triples from `generated_graph.ttl`.")
        st.code("\n".join(triples["triples"]), language="turtle")
        turtle_export = api_get_text(api_url, "/rdf-turtle") if backend_online else None
        if turtle_export:
            st.download_button("Export RDF Turtle", turtle_export, "generated_graph.ttl", "text/turtle")

with tab_inference:
    st.header("4. Inferred risk labels and RDF facts")
    st.write(
        "The reasoning service adds new RDF facts such as `oc:HighRiskWallet`, "
        "`oc:SuspiciousTransaction`, and `oc:SuspiciousContract`. These labels are explainable because each one stores "
        "`oc:riskExplanation` text and links to risk indicators and fraud patterns."
    )
    summary = api_get(api_url, "/risk-summary") if backend_online else None
    if summary:
        render_metric_row(summary)
        st.subheader("High-risk wallets")
        st.dataframe(risk_dataframe(summary.get("high_risk_wallets", [])), use_container_width=True)
        st.subheader("Suspicious transactions")
        st.dataframe(risk_dataframe(summary.get("suspicious_transactions", [])), use_container_width=True)
        st.subheader("Suspicious smart contracts")
        st.dataframe(risk_dataframe(summary.get("suspicious_contracts", [])), use_container_width=True)
        st.info(
            "Presentation point: these are not manually typed labels. They are inferred and stored back into the RDF graph."
        )
        risk_csv = api_get_text(api_url, "/risk-summary.csv") if backend_online else None
        if risk_csv:
            st.download_button("Export risk summary CSV", risk_csv, "risk_summary.csv", "text/csv")
    st.subheader("Inferred RDF facts")
    inferred_payload = api_get(api_url, "/inferred-facts") if backend_online else None
    if inferred_payload:
        st.write(f"Inferred facts returned: {inferred_payload.get('inferred_fact_count', 0)}")
        st.dataframe(inferred_fact_dataframe(inferred_payload.get("facts", [])), use_container_width=True)

with tab_evidence:
    st.header("5. Evidence-based risk explanation")
    st.write(
        "Select an inferred risk entity to inspect the matched rule, original source triples, inferred triples, "
        "and a SPARQL evidence query. This makes the classification defendable during Q&A."
    )
    summary = api_get(api_url, "/risk-summary") if backend_online else None
    if summary:
        options = risk_entity_options(summary)
        if options:
            selected_label = st.selectbox("Risk entity", list(options))
            evidence = api_get(api_url, "/risk-evidence", entity_id=options[selected_label])
            if evidence:
                st.subheader(f"{evidence.get('label')} ({evidence.get('type')})")
                st.metric("Risk score", evidence.get("riskScore"))
                st.write("Rule explanations")
                st.dataframe(pd.DataFrame(evidence.get("matchedRules", [])), use_container_width=True)
                st.write("Source RDF triples")
                st.code("\n".join(evidence.get("sourceTriples", [])) or "No source triples found.", language="turtle")
                st.write("Inferred RDF triples")
                st.code("\n".join(evidence.get("inferredTriples", [])) or "No inferred triples found.", language="turtle")
                st.write("SPARQL evidence query")
                st.code(evidence.get("sparqlEvidenceQuery", ""), language="sparql")
        else:
            st.info("No inferred risk entities are available yet. Build the RDF knowledge graph first.")

with tab_sparql:
    st.header("6. SPARQL query results")
    st.write(
        "SPARQL queries retrieve both original CSV-derived facts and inferred risk classifications from the same RDF graph."
    )
    selected_query = st.selectbox("Predefined query", list(PREDEFINED_QUERIES))
    st.info(PREDEFINED_QUERIES[selected_query]["question"])
    query_text = st.text_area("SPARQL", PREDEFINED_QUERIES[selected_query]["query"], height=260)
    if st.button("Run SPARQL query"):
        result = api_post(api_url, "/query-sparql", json={"query": query_text})
        if result:
            st.session_state["sparql_result"] = result
            st.write(f"Rows returned: {result['row_count']}")
            result_frame = query_result_dataframe(result["rows"])
            st.dataframe(result_frame, use_container_width=True)
            st.download_button("Export SPARQL result CSV", csv_bytes_from_frame(result_frame), "sparql_result.csv", "text/csv")
    elif "sparql_result" in st.session_state:
        previous_frame = query_result_dataframe(st.session_state["sparql_result"].get("rows", []))
        st.caption("Last SPARQL result is available for export.")
        st.download_button("Export last SPARQL result CSV", csv_bytes_from_frame(previous_frame), "sparql_result.csv", "text/csv")

with tab_graph:
    st.header("7. Knowledge graph visualisation")
    st.write(
        "The graph view shows RDF resources as nodes and object properties as labelled edges. "
        "Risk nodes and inferred classifications are visualised together with original transaction facts."
    )
    graph_filter_labels = {
        "All RDF relationships": "all",
        "Risk entities only": "risk_entities",
        "Wallet transfers": "wallet_transfers",
        "Smart contract interactions": "contract_interactions",
        "Inferred risk relationships": "inferred_relationships",
    }
    selected_filter_label = st.selectbox("Graph filter", list(graph_filter_labels))
    graph_payload = api_get(api_url, "/graph-data", filter_mode=graph_filter_labels[selected_filter_label]) if backend_online else None
    if graph_payload:
        st.caption("Colours indicate resource types such as Wallet, Transaction, SmartContract, RiskIndicator, and FraudPattern.")
        st.write(f"Nodes: {len(graph_payload.get('nodes', []))} | Edges: {len(graph_payload.get('edges', []))}")
        render_graph(graph_payload)

with tab_explain:
    st.header("8. How the system uses Semantic Web technology")
    st.write("Use this section during Q&A to connect the software demo directly to the TSW6223 rubric.")

    st.subheader("RDF")
    st.write(
        "The CSV is converted into RDF triples with stable URIs. For example, a transaction resource links to wallets using "
        "`oc:involvesWallet`, to a token using `oc:usesToken`, and to a contract using `oc:interactsWithContract`."
    )

    st.subheader("RDFS and OWL ontology")
    st.write(
        "`ontology.ttl` defines classes such as `oc:Wallet`, `oc:Transaction`, `oc:SmartContract`, "
        "`oc:HighRiskWallet`, and `oc:SuspiciousTransaction`. It also defines object properties, data properties, "
        "domains, ranges, subclass relationships, labels, and comments."
    )

    st.subheader("Inference")
    st.write(
        "Rule-based reasoning creates new semantic facts. Example: if a wallet sends to a mixer wallet, it is classified "
        "as `oc:HighRiskWallet`, linked to a risk indicator, and given an `oc:riskExplanation` literal explaining why."
    )

    st.subheader("SPARQL")
    st.write(
        "The SPARQL tab demonstrates semantic querying over the graph, including queries that return inferred classes and "
        "their explanation triples."
    )
