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

5. Open the **Validation** tab or click **Validate CSV** in the sidebar.

   - Explain that the system checks the required ontology-mapped CSV fields before RDF generation.
   - Point out that invalid numeric amounts or missing required values are reported before the graph is built.
   - State that this supports demo stability and data quality for CSV-to-RDF conversion.

6. Click **Build RDF knowledge graph** in the sidebar. Do not upload a file for the standard demo. This uses `backend/data/sample_transactions.csv`.

7. Open the **RDF triples** tab and explain the generated RDF:

   - Wallets, transactions, tokens, and contracts are RDF resources.
   - Relationships such as `oc:sentTo`, `oc:usesToken`, and `oc:interactsWithContract` are object properties.
   - Literal values such as `oc:amount`, `oc:timestamp`, and `oc:riskScore` are data properties.
   - The generated Turtle graph is stored in `backend/data/generated_graph.ttl`.
   - Use **Export RDF Turtle** if the marker wants to inspect the generated `.ttl` output.

8. Open the **Inferred facts** tab and explain the risk summary:

   - `0xAlice` is high risk because its `oc:riskExplanation` says it interacted with a `MixerWallet`.
   - `0xBob` is high risk because its `oc:riskExplanation` says it sent transactions to three or more risky wallets.
   - High-value transactions above 10000 are suspicious because their explanation says the amount threshold was exceeded.
   - `0xRiskyContract` is suspicious because its explanation says it received repeated high-value transactions.
   - Each inferred entity has a risk explanation, risk indicator, fraud pattern, and risk score to support explainability.
   - Show the **Inferred RDF facts** table to prove that reasoning results are stored as triples, not only as UI text.
   - Use **Export risk summary CSV** if needed for report evidence.

9. Open the **Risk evidence** tab.

   - Select `Wallet: 0xAlice` or `Wallet: 0xBob`.
   - Show the matched rule explanation.
   - Show source RDF triples from the original CSV-derived facts.
   - Show inferred RDF triples such as `rdf:type oc:HighRiskWallet`, `oc:riskScore`, and `oc:riskExplanation`.
   - Show the SPARQL evidence query and explain that the classification can be verified semantically.

10. Open the **SPARQL** tab and run the predefined queries:

   - High-risk wallets with explanations
   - Suspicious transactions with explanations
   - Wallet-to-wallet transfers
   - Smart contract interactions
   - All inferred facts
   - Ontology classes used in the graph
   - Mixer exposure relationships
   - Point out the short explanation beside each preset query before running it.
   - Use **Export SPARQL result CSV** to show that query results can be reused.

11. Open the **Knowledge graph** tab.

   - Point out Wallet, Transaction, Token, SmartContract, RiskIndicator, and FraudPattern nodes.
   - Explain that labelled edges are RDF object properties.
   - Mention that inferred risk nodes are part of the same RDF graph as the original CSV data.
   - Use the graph filter to switch between all relationships, wallet transfers, smart contract interactions, and inferred risk relationships.

12. Open the **Semantic Web use** tab.

    - Use it as the final rubric summary.
    - Category 2 is demonstrated through RDF triples, RDFS modelling, and SPARQL queries.
    - Category 3 is demonstrated through OWL ontology classes/properties and rule-based inference.

13. For Q&A, open `backend/data/generated_graph.ttl` or use **Export RDF Turtle** to show that the demo produces real Turtle RDF output.

14. Mention that the automated tests validate CSV validation, RDF conversion, ontology loading, reasoning rules, SPARQL queries, evidence output, graph filtering, and API output formats.

## Five-Minute Presentation Flow

1. **Minute 1: Problem and raw data**
   - State the problem: flat blockchain transaction tables do not explain wallet, contract, and risk relationships well.
   - Show **Raw CSV** and identify sender, receiver, amount, contract, token, and transaction type.

2. **Minute 2: Validation and RDF graph construction**
   - Show **Validation** and explain data-quality checks before RDF conversion.
   - Click **Build RDF knowledge graph**.
   - Show **RDF triples**.
   - Explain that wallets, transactions, tokens, and contracts are RDF resources connected by object properties.

3. **Minute 3: OWL/RDFS and inference**
   - Show **Inferred facts**.
   - Explain that `HighRiskWallet`, `SuspiciousTransaction`, and `SuspiciousContract` are ontology classes.
   - Read the `oc:riskExplanation` values for `0xAlice`, `0xBob`, high-value transactions, and `0xRiskyContract`.
   - Show one inferred RDF fact row.

4. **Minute 4: Evidence, SPARQL and graph visualisation**
   - Open **Risk evidence** for `0xAlice` and show source triples plus inferred triples.
   - Run **High-risk wallets with explanations**.
   - Run **Ontology classes used in graph** or **All inferred facts**.
   - Show **Knowledge graph** and use one graph filter.

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

**Q7: How do you prove a risk label is explainable?**

A: The Risk evidence tab shows the source RDF triples, the inferred RDF triples, the matched rule explanation, and a SPARQL evidence query for the selected entity.

**Q8: How is uploaded data checked before RDF generation?**

A: The Validation tab checks required columns, missing required values, numeric amounts, timestamp warnings, and transaction type warnings before building the graph.

**Q9: Can custom queries be used?**

A: Yes. The SPARQL tab includes predefined queries for the demo, but the query text area remains editable for custom SPARQL.

**Q10: What are the limitations?**

A: The MVP uses sample CSV data, simple transparent rules, and a compact ontology. It does not use live blockchain crawling or production-grade fraud scoring.

**Q11: How was the system evaluated?**

A: Automated tests validate semantic CSV validation, CSV-to-RDF conversion, ontology loading, each reasoning rule, SPARQL query output, graph-data format, risk-summary format, inferred facts, and risk evidence output.

**Q12: What future improvements are possible?**

A: Future work could add formal SHACL validation, named graphs, more fraud patterns, pagination for larger graphs, and eventually real blockchain datasets.

## If the Backend Is Not Running

The Streamlit UI shows a friendly warning. Start FastAPI with:

```bash
uvicorn backend.main:app --reload
```
