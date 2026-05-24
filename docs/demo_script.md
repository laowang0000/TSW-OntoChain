# Demo Script

This script is designed for a short university presentation and demonstration. The goal is to show Semantic Web technology clearly, not to present a generic cryptocurrency dashboard.

## Setup Before Presentation

Recommended setup:

1. Double-click `SETUP_ENV.bat` once before the presentation day.
2. Double-click `START_ONTOCHAIN.bat` to start both services.
3. Open `http://127.0.0.1:8501` if the browser does not open automatically.

Manual setup:

1. Start the backend:

   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. Start the frontend in another terminal:

   ```bash
   python -m streamlit run frontend/streamlit_app.py
   ```

3. Open the Streamlit page and keep the default FastAPI URL as `http://localhost:8000`.

## Step-By-Step Demonstration

4. Open the **Raw CSV** tab.

   - Explain that the table is ordinary blockchain transaction data.
   - Point out the required fields: `tx_hash`, `sender`, `receiver`, `token`, `amount`, `timestamp`, `contract_address`, and `transaction_type`.
   - State that the system will convert these rows into RDF resources and triples.

5. Click **Build RDF knowledge graph** in the sidebar. Do not upload a file for the standard demo. This uses `backend/data/sample_transactions.csv`.

6. Open the **RDF triples** tab and explain the generated RDF:

   - Wallets, transactions, tokens, and contracts are RDF resources.
   - Relationships such as `oc:sentTo`, `oc:usesToken`, and `oc:interactsWithContract` are object properties.
   - Literal values such as `oc:amount`, `oc:timestamp`, and `oc:riskScore` are data properties.
   - The generated Turtle graph is stored in `backend/data/generated_graph.ttl`.

7. Open the **Inferred risks** tab and explain the risk summary:

   - `0xAlice` is high risk because its `oc:riskExplanation` says it interacted with a `MixerWallet`.
   - `0xBob` is high risk because its `oc:riskExplanation` says it sent transactions to three or more risky wallets.
   - High-value transactions above 10000 are suspicious because their explanation says the amount threshold was exceeded.
   - `0xRiskyContract` is suspicious because its explanation says it received repeated high-value transactions.
   - Each inferred entity has a risk explanation, risk indicator, fraud pattern, and risk score to support explainability.

8. Open the **SPARQL** tab and run the predefined queries:

   - High-risk wallets with explanations
   - Suspicious transactions with explanations
   - Wallet-to-wallet transfers
   - Smart contract interactions
   - All inferred facts
   - Ontology classes used in the graph
   - Mixer exposure relationships
   - Point out the short explanation beside each preset query before running it.

9. Open the **Knowledge graph** tab.

   - Point out Wallet, Transaction, Token, SmartContract, RiskIndicator, and FraudPattern nodes.
   - Explain that labelled edges are RDF object properties.
   - Mention that inferred risk nodes are part of the same RDF graph as the original CSV data.

10. Open the **Semantic Web use** tab.

    - Use it as the final rubric summary.
    - Category 2 is demonstrated through RDF triples, RDFS modelling, and SPARQL queries.
    - Category 3 is demonstrated through OWL ontology classes/properties and rule-based inference.

11. For Q&A, open `backend/data/generated_graph.ttl` to show that the demo produces real Turtle RDF output.

12. Mention that the automated tests validate the RDF conversion, ontology loading, reasoning rules, SPARQL queries, and API output formats.

## Five-Minute Presentation Flow

1. **Minute 1: Problem and raw data**
   - State the problem: flat blockchain transaction tables do not explain wallet, contract, and risk relationships well.
   - Show **Raw CSV** and identify sender, receiver, amount, contract, token, and transaction type.

2. **Minute 2: RDF graph construction**
   - Click **Build RDF knowledge graph**.
   - Show **RDF triples**.
   - Explain that wallets, transactions, tokens, and contracts are RDF resources connected by object properties.

3. **Minute 3: OWL/RDFS and inference**
   - Show **Inferred risks**.
   - Explain that `HighRiskWallet`, `SuspiciousTransaction`, and `SuspiciousContract` are ontology classes.
   - Read the `oc:riskExplanation` values for `0xAlice`, `0xBob`, high-value transactions, and `0xRiskyContract`.

4. **Minute 4: SPARQL and graph visualisation**
   - Run **High-risk wallets with explanations**.
   - Run **Ontology classes used in graph** or **All inferred facts**.
   - Show **Knowledge graph** and point out labelled RDF relationships.

5. **Minute 5: Rubric alignment**
   - Open **Semantic Web use**.
   - State that Category 2 is shown through RDF/RDFS/SPARQL.
   - State that Category 3 is shown through OWL ontology and rule-based inference.
   - Mention that tests validate RDF conversion, ontology loading, reasoning, SPARQL, and API output.

## Expected Q&A

**Q1: Why is this a Semantic Web project rather than a normal dashboard?**

A: The core output is an RDF knowledge graph. The system uses ontology classes and properties, stores inferred facts as RDF triples, and queries them with SPARQL. A dashboard would only display values; OntoChain models meaning and derives new semantic facts.

**Q2: Which project categories are demonstrated?**

A: Category 2 is demonstrated through RDF triples, RDFS modelling, and SPARQL queries. Category 3 is demonstrated through OWL classes/properties and rule-based inference.

**Q3: Why use RDF for blockchain data?**

A: Blockchain data is relationship-heavy. RDF naturally represents relationships such as wallet-to-wallet transfers, transactions using tokens, and transactions interacting with smart contracts.

**Q4: What does OWL add here?**

A: OWL defines formal classes and properties such as `Wallet`, `Transaction`, `SmartContract`, `HighRiskWallet`, `SuspiciousTransaction`, `sentTo`, and `riskExplanation`.

**Q5: Is the system using machine learning?**

A: No. The project uses transparent rule-based inference. This is suitable for the assignment because every risk label can be explained with RDF triples and SPARQL.

**Q6: How are inferred facts stored?**

A: Inferred facts are written back into the RDF graph. For example, a wallet can receive `rdf:type oc:HighRiskWallet` and `oc:riskExplanation "Wallet classified as HighRiskWallet because it interacted with a MixerWallet."`

**Q7: Can custom queries be used?**

A: Yes. The SPARQL tab includes predefined queries for the demo, but the query text area remains editable for custom SPARQL.

**Q8: What are the limitations?**

A: The MVP uses sample CSV data, simple transparent rules, and a compact ontology. It does not use live blockchain crawling or production-grade fraud scoring.

**Q9: How was the system evaluated?**

A: Automated tests validate CSV-to-RDF conversion, ontology loading, each reasoning rule, SPARQL query output, graph-data format, and risk-summary format.

**Q10: What future improvements are possible?**

A: Future work could add SHACL validation, named graphs, more fraud patterns, larger graph filtering, export functions, and eventually real blockchain datasets.

## If the Backend Is Not Running

The Streamlit UI shows a friendly warning. Start FastAPI with:

```bash
uvicorn backend.main:app --reload
```
