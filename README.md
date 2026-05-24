# OntoChain: Semantic Blockchain Risk System

OntoChain is a university MVP for **TSW6223 Semantic Web Technology**. It converts blockchain transaction CSV data into RDF triples, applies an OWL/RDFS ontology plus rule-based inference, exposes SPARQL queries, and visualises the resulting knowledge graph.

The project is intentionally not a generic cryptocurrency dashboard. Its main purpose is to demonstrate **Category 2: RDF, RDFS, SPARQL** and **Category 3: OWL and/or inference**.

## Problem Statement

Blockchain transaction data is usually stored as flat tables or explorer-style records. This makes it easy to list transactions, but harder to explain relationships such as which wallets interacted with mixers, which transactions are high value, which smart contracts repeatedly receive risky activity, and why a wallet or contract is classified as suspicious.

OntoChain addresses this by turning transaction data into a semantic knowledge graph. The system models wallets, transactions, tokens, and smart contracts as RDF resources, then uses ontology terms and inference rules to add explainable risk classifications.

## Objectives

- Convert blockchain transaction CSV data into RDF triples.
- Define an OWL/RDFS ontology for wallets, transactions, smart contracts, tokens, risk indicators, and fraud patterns.
- Apply rule-based inference to classify high-risk wallets, suspicious transactions, and suspicious contracts.
- Query both original and inferred facts using SPARQL.
- Visualise the knowledge graph for a clear university demonstration.

## Selected Semantic Web Categories

- **Category 2: RDF, RDFS, SPARQL**
  - RDF represents blockchain records as subject-predicate-object triples.
  - RDFS labels, comments, subclass relationships, domains, and ranges make the vocabulary meaningful.
  - SPARQL retrieves relationships and inferred risk facts from the generated graph.
- **Category 3: OWL and/or inference**
  - OWL classes and properties are defined in `backend/data/ontology.ttl`.
  - Rule-based inference adds new semantic facts such as `oc:HighRiskWallet`, `oc:SuspiciousTransaction`, `oc:SuspiciousContract`, and `oc:riskExplanation`.

## Why These Technologies Were Chosen

- **RDF** was chosen because blockchain transactions naturally form graph relationships: wallets send to wallets, transactions use tokens, and transactions interact with contracts.
- **RDFS** was chosen to make the graph understandable by defining class hierarchy and property meaning.
- **OWL** was chosen to express the ontology as formal semantic vocabulary rather than plain Python objects.
- **SPARQL** was chosen because it demonstrates semantic querying across original facts and inferred facts in one graph.
- **Inference** was chosen because the project must show more than storage: the system derives new risk classifications from existing transaction facts.

## Project Structure

```text
semantic-blockchain-risk-system/
+-- backend/
|   +-- main.py
|   +-- services/
|   +-- data/
+-- frontend/
+-- tests/
+-- docs/
+-- requirements.txt
+-- README.md
```

## System Architecture

```text
CSV transaction data
        |
        v
RDF builder (RDFLib)
        |
        v
OWL/RDFS ontology + generated RDF graph
        |
        v
Rule-based reasoning
        |
        v
Inferred RDF facts + risk explanations
        |
        +--> FastAPI endpoints
        +--> SPARQL queries
        +--> Streamlit demo UI
        +--> Knowledge graph visualisation
```

Main components:

- `backend/services/rdf_builder.py` converts CSV rows into RDF triples.
- `backend/data/ontology.ttl` defines the OWL/RDFS vocabulary.
- `backend/services/reasoning_service.py` applies inference rules.
- `backend/services/sparql_service.py` executes SPARQL queries.
- `backend/services/graph_service.py` prepares risk summaries and graph visualisation data.
- `frontend/streamlit_app.py` provides the demonstration interface.

## Setup

Recommended on Windows:

1. Double-click `SETUP_ENV.bat`.
2. Wait until it prints `OntoChain environment OK`.
3. Then double-click `START_ONTOCHAIN.bat`.

`SETUP_ENV.bat` creates a local `.venv` virtual environment and installs all packages from `requirements.txt`. `START_ONTOCHAIN.bat` opens two service windows: one for FastAPI and one for Streamlit.

Manual setup:

```bash
cd semantic-blockchain-risk-system
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the Backend

If you use `START_ONTOCHAIN.bat`, this is started automatically.

```bash
python -m uvicorn backend.main:app --reload
```

Open the API docs at `http://localhost:8000/docs`.

## Run the Frontend

If you use `START_ONTOCHAIN.bat`, this is started automatically.

In a second terminal for manual startup:

```bash
python -m streamlit run frontend/streamlit_app.py
```

Use the default FastAPI URL, then click **Build RDF knowledge graph**.

The Streamlit app is organised as a guided university presentation:

1. **Raw CSV** - shows the original blockchain transaction table.
2. **RDF triples** - shows Turtle-style triples generated from the CSV.
3. **Inferred risks** - shows high-risk wallets, suspicious transactions, and suspicious contracts with rule explanations.
4. **SPARQL** - runs predefined or custom SPARQL queries over the graph.
5. **Knowledge graph** - visualises resources and object-property edges.
6. **Semantic Web use** - gives short talking points for RDF, RDFS/OWL, inference, and SPARQL.

If the backend is not running, the UI shows a friendly message with the command needed to start FastAPI.

## Troubleshooting

### `ModuleNotFoundError: No module named 'pyvis'`

This means Streamlit is running in a Python environment where `pyvis` is not installed. Install the project dependencies in the same terminal/Python environment used to run Streamlit:

```bash
python -m pip install -r requirements.txt
```

Or install only the missing graph visualisation dependency:

```bash
python -m pip install pyvis==0.3.2
```

The app now shows a friendly message in the graph tab if `pyvis` is missing, but installing it is recommended for the full knowledge graph visualisation.

## FastAPI Endpoints

- `GET /` - health and endpoint guide
- `POST /build-graph` - build RDF from uploaded CSV or sample CSV and apply reasoning
- `GET /triples` - show generated RDF triples
- `POST /query-sparql` - run SPARQL queries
- `GET /risk-summary` - return inferred risk counts and explanations
- `GET /graph-data` - return nodes and edges for visualisation

## Semantic Web Features

### RDF

`rdf_builder.py` converts each CSV row into RDF resources and triples. For example:

- Wallets become `oc:Wallet`
- Transactions become `oc:Transaction`
- Tokens become `oc:Token`
- Contracts become `oc:SmartContract`
- Relationships use object properties such as `oc:sentTo`, `oc:usesToken`, and `oc:interactsWithContract`

### RDFS and OWL

`backend/data/ontology.ttl` defines classes, subclass relationships, object properties, data properties, domains, ranges, labels, and comments. Examples include:

- `oc:MixerWallet rdfs:subClassOf oc:Wallet`
- `oc:HighRiskWallet rdfs:subClassOf oc:Wallet`
- `oc:SuspiciousTransaction rdfs:subClassOf oc:Transaction`
- `oc:sentTo` as an OWL object property
- `oc:amount` and `oc:riskScore` as OWL data properties
- `oc:riskExplanation` as an OWL data property that stores the rule explanation for inferred risk labels

### Inference

`reasoning_service.py` applies rule-based inference and writes inferred triples back into the graph:

- A wallet that interacts with a mixer is classified as `oc:HighRiskWallet`
- A transaction above 10000 is classified as `oc:SuspiciousTransaction`
- A wallet that sends to three or more risky wallets is classified as `oc:HighRiskWallet`
- A smart contract with repeated high-value transactions is classified as `oc:SuspiciousContract`

Each inferred entity also receives an `oc:riskExplanation` literal, such as `Wallet classified as HighRiskWallet because it interacted with a MixerWallet.` This makes the classification explainable in RDF, the API, Streamlit, and SPARQL.

### SPARQL

Users can run custom SPARQL queries through the Streamlit UI or `POST /query-sparql`. The frontend also includes predefined semantic questions for:

- high-risk wallets with risk scores and explanations
- suspicious transactions with amounts and explanations
- wallet-to-wallet transfer relationships
- smart contract interactions
- all inferred risk facts
- ontology classes that have instances in the generated graph

Example:

```sparql
SELECT ?wallet ?label ?score ?explanation
WHERE {
  ?wallet a oc:HighRiskWallet ;
          rdfs:label ?label ;
          oc:riskScore ?score ;
          oc:riskExplanation ?explanation .
}
ORDER BY DESC(?score)
```

## Test

```bash
pytest
```

The tests are designed to support project marking and Q&A. They cover:

- CSV-to-RDF conversion, including transaction literals and wallet relationships
- Ontology loading for required OWL/RDFS classes and properties
- Rule-based reasoning for high-value transactions, mixer interaction, repeated risky-wallet interaction, and suspicious contracts
- SPARQL queries for high-risk wallets, suspicious transactions, and risk explanations
- API output shapes for `GET /graph-data` and `GET /risk-summary`

The tests use the bundled sample data or temporary CSV files, so they do not depend on absolute machine-specific paths.

## Evaluation

The system is evaluated through automated tests and manual demonstration:

- RDF generation is checked by verifying resources, literals, and wallet transfer relationships.
- Ontology loading is checked by verifying OWL classes and properties.
- Reasoning is checked by testing each inference rule separately.
- SPARQL is checked by querying high-risk wallets, suspicious transactions, transfer relationships, inferred facts, and ontology classes.
- API output is checked for graph-data and risk-summary response format.
- Streamlit demonstration is checked by building the graph, showing triples, running SPARQL, and viewing the knowledge graph.

## Demo Flow

1. Start FastAPI.
2. Start Streamlit.
3. Open **Raw CSV** and explain the source transaction fields.
4. Click **Build RDF knowledge graph**.
5. Open **RDF triples** and show the generated Turtle facts.
6. Open **Inferred risks** and explain the `oc:riskExplanation` text for each rule-based classification.
7. Open **SPARQL** and run a predefined query.
8. Open **Knowledge graph** and show how entities are connected.
9. Open **Semantic Web use** to connect the demo to RDF, RDFS/OWL, inference, and SPARQL.

More detail is available in `docs/demo_script.md`, `docs/architecture.md`, and `docs/sparql_examples.md`.

## Limitations

- The project uses sample CSV data rather than a live blockchain node or external blockchain API.
- The inference rules are transparent and rule-based, not machine learning predictions.
- The ontology is compact and designed for demonstration, not a complete blockchain fraud ontology.
- Wallet labels such as mixer or exchange are inferred from sample transaction types for MVP clarity.
- Risk scores are demo values used to rank inferred risks, not production financial risk scores.

## Future Improvements

- Add more ontology classes for phishing wallets, bridge contracts, token approvals, and sanction indicators.
- Support larger datasets with pagination and graph filtering.
- Add export buttons for SPARQL results and risk summaries.
- Add optional SHACL validation for uploaded CSV-to-RDF data quality.
- Add named graphs to separate source facts, ontology facts, and inferred facts.
- Connect to real blockchain datasets only after the Semantic Web MVP is stable.

## Rubric Alignment

- **Knowledge and Understanding**: The project explains why RDF, RDFS, SPARQL, OWL, and inference fit blockchain risk analysis. The UI and docs show how each technology is used.
- **Organisation**: The project is separated into backend services, ontology/data files, frontend demo, tests, and documentation.
- **Format**: Documentation follows the report topics: problem statement, solution development, evaluation, limitations, future improvements, and references-ready technical explanation.
- **Innovation**: The project applies Semantic Web technology to blockchain fraud and smart contract risk analysis rather than building a generic crypto dashboard.
- **Clarity in Software**: Code is modular, documented, and supported by tests for RDF generation, ontology loading, reasoning, SPARQL, and API output.
- **Demonstration**: Streamlit provides a clear flow from raw CSV to RDF triples, inferred risks, SPARQL queries, and graph visualisation.
- **Teamwork Support**: The structure allows group members to divide work by ontology, backend services, frontend demo, testing, and report writing.
