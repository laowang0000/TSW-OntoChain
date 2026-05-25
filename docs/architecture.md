# OntoChain Architecture

OntoChain is designed to demonstrate Category 2 and Category 3 Semantic Web technologies in a working blockchain risk analysis MVP.

## Problem Context

Blockchain transaction records are relational and graph-like: a wallet sends to another wallet, a transaction uses a token, and a transaction interacts with a smart contract. A flat CSV can store these values, but it does not directly express semantic meaning or support inference.

OntoChain converts transaction rows into a semantic knowledge graph so risk classifications can be explained using RDF triples, ontology terms, and SPARQL queries.

## Semantic Web Scope

- **Category 2: RDF/RDFS/SPARQL** - CSV transaction rows are converted into RDF triples using RDFLib. The ontology defines RDFS labels, comments, domains, ranges, and subclass relationships. Users can run SPARQL queries over both source facts and inferred facts.
- **Category 3: OWL and inference** - `ontology.ttl` defines OWL classes and object/data properties. The reasoning service applies transparent rule-based inference and writes new RDF statements, such as `rdf:type oc:HighRiskWallet` and `rdf:type oc:SuspiciousTransaction`.

## Why RDF/RDFS/SPARQL and OWL/Inference

- RDF is suitable because wallet and transaction relationships are naturally graph-shaped.
- RDFS is used so classes and properties have labels, comments, subclass relationships, domains, and ranges.
- OWL is used to formally define ontology classes and properties in Turtle.
- SPARQL is used to ask semantic questions that combine original transaction facts and inferred risk facts.
- Inference is used to derive classifications that are not directly present in the CSV.

## Data Flow

1. A CSV file is uploaded or the bundled sample file is used.
2. `validation_service.py` checks required columns, missing values, numeric amounts, timestamp warnings, and transaction type warnings.
3. `rdf_builder.py` creates RDF resources for wallets, transactions, tokens, and contracts.
4. `ontology_service.py` loads `ontology.ttl` and binds namespaces for readable Turtle output.
5. `reasoning_service.py` applies the fraud/risk rules and inserts inferred triples, including human-readable `oc:riskExplanation` literals.
6. `generated_graph.ttl` stores the ontology, source facts, and inferred facts in Turtle.
7. FastAPI exposes validation, triples, inferred facts, SPARQL, risk summaries, evidence views, exports, and graph visualisation data.
8. Streamlit provides a guided demo UI for validation, graph building, SPARQL execution, evidence explanation, exports, and pyvis visualisation.

## Runtime Components

| Component | File | Responsibility |
| --- | --- | --- |
| FastAPI app | `backend/main.py` | Exposes build, triples, SPARQL, risk summary, and graph-data endpoints. |
| Validation service | `backend/services/validation_service.py` | Checks uploaded transaction CSV files before RDF generation. |
| RDF builder | `backend/services/rdf_builder.py` | Converts CSV rows into RDF triples. |
| Ontology service | `backend/services/ontology_service.py` | Loads `ontology.ttl`, binds namespaces, and saves generated Turtle. |
| Reasoning service | `backend/services/reasoning_service.py` | Applies rule-based inference and writes explanation triples. |
| SPARQL service | `backend/services/sparql_service.py` | Executes SPARQL queries with default prefixes. |
| Graph service | `backend/services/graph_service.py` | Creates risk summaries, inferred facts, risk evidence, and filtered visualisation data. |
| Streamlit UI | `frontend/streamlit_app.py` | Provides a guided presentation interface. |

## Semantic Validation

The validation layer is intentionally simple and visible. It checks whether a CSV can be mapped into the ontology-driven RDF graph before RDF generation starts. It reports:

- missing required columns
- empty required values
- non-numeric `amount` values
- timestamp format warnings
- transaction type warnings

This supports the rubric by showing software clarity and data-quality control before semantic graph construction.

## Core Classes

The ontology includes `Wallet`, `Transaction`, `Token`, `SmartContract`, `ExchangeWallet`, `MixerWallet`, `HighRiskWallet`, `SuspiciousTransaction`, `RiskIndicator`, and `FraudPattern`. It also includes `SuspiciousContract` because one required reasoning rule classifies contracts.

## Reasoning Rules

- Wallets that interact with a `MixerWallet` become `HighRiskWallet`.
- Transactions with `oc:amount` greater than 10000 become `SuspiciousTransaction`.
- Wallets that send to three or more risky wallets become `HighRiskWallet`.
- Smart contracts that receive three or more high-value transactions become `SuspiciousContract`.

Each rule also adds `oc:hasRiskIndicator`, `oc:classifiedAs`, `oc:riskScore`, and `oc:riskExplanation` triples so the demo can explain the classification.

## Explainable Risk Classification

Risk explanations are stored in RDF rather than only being produced in the UI. This means a classification can be defended with SPARQL, for example:

- `oc:riskExplanation "Wallet classified as HighRiskWallet because it interacted with a MixerWallet."`
- `oc:riskExplanation "Transaction classified as SuspiciousTransaction because amount is greater than 10000."`
- `oc:riskExplanation "Wallet classified as HighRiskWallet because it sent transactions to three or more risky wallets."`
- `oc:riskExplanation "SmartContract classified as SuspiciousContract because it received repeated high-value transactions."`

The same explanation triples appear in `GET /risk-summary`, the Streamlit risk tables, and `generated_graph.ttl`.

The evidence view expands each explanation into:

- matched risk rule details
- source RDF triples that came from CSV facts
- inferred RDF triples added by reasoning
- a SPARQL evidence query for the selected entity

This makes the inference path easier to defend during Q&A.

## Export and Graph Filtering

The frontend exposes lightweight export actions for generated Turtle RDF, risk summary CSV, and SPARQL result CSV. These exports are demo support features: they do not change the semantic model, but they make RDF and query results easier to inspect and include in the report.

The graph-data endpoint supports filters for all relationships, risk entities, wallet transfers, smart contract interactions, and inferred risk relationships. This keeps the visualisation readable during a short presentation.

## Testing and Evaluation

The test suite checks the architecture from multiple levels:

- CSV-to-RDF conversion preserves transaction fields and relationships.
- CSV validation catches missing columns and invalid numeric amounts before RDF conversion.
- Ontology loading confirms required OWL/RDFS classes and properties exist.
- Reasoning tests confirm each rule creates the expected inferred RDF type and risk indicator.
- SPARQL tests confirm semantic queries can retrieve high-risk wallets, suspicious transactions, transfer relationships, contract interactions, inferred facts, and ontology classes.
- API output tests confirm `GET /risk-summary`, `GET /graph-data`, `GET /inferred-facts`, and `GET /risk-evidence` return predictable structures for the frontend.

## Limitations and Future Work

Current limitations:

- The MVP uses sample CSV data and does not connect to a live blockchain node.
- Risk rules are intentionally simple for explainability.
- The ontology is compact and focused on the assignment scope.
- Graph visualisation is best suited for small demonstration datasets.

Future improvements:

- Add named graphs to distinguish ontology, source facts, and inferred facts.
- Convert the current CSV validation checks into formal SHACL shapes.
- Add more fraud patterns, such as phishing, rapid fund splitting, or suspicious token approvals.
- Add pagination and search for larger datasets.
- Connect to real blockchain datasets after the semantic workflow is fully validated.
