# Change Log

This file records meaningful project changes for traceability, rubric alignment, and teamwork discussion.

## 2026-05-26 - Evidence, Validation, Inferred Facts, Exports, and Graph Filtering

**Goal**

Strengthen OntoChain for highest-score demonstration by adding evidence-based risk explanation, semantic CSV validation, clearer inferred facts, export support, and graph filtering.

**Files changed**

- `.gitignore`
- `backend/main.py`
- `backend/services/graph_service.py`
- `backend/services/validation_service.py`
- `frontend/streamlit_app.py`
- `tests/test_api_outputs.py`
- `tests/test_validation.py`
- `README.md`
- `docs/architecture.md`
- `docs/demo_script.md`
- `docs/sparql_examples.md`
- `docs/change_log.md`

**Added**

- `POST /validate-csv` endpoint for CSV structure and value checks before RDF generation.
- `GET /inferred-facts` endpoint for RDF facts added by reasoning.
- `GET /risk-evidence` endpoint for matched rules, source triples, inferred triples, and SPARQL evidence query.
- `GET /rdf-turtle` and `GET /risk-summary.csv` export endpoints.
- Graph filters for all relationships, risk entities, wallet transfers, smart contract interactions, and inferred risk relationships.
- Streamlit Validation, Inferred Facts, Risk Evidence, export buttons, SPARQL result export, and graph filter controls.
- Tests for validation, inferred facts, risk evidence, and graph filtering.

**Modified**

- `POST /build-graph` now validates the selected CSV before RDF generation and returns the validation report.
- Streamlit demo flow now follows raw data -> validation -> RDF -> inferred facts -> risk evidence -> SPARQL -> graph -> rubric explanation.
- Documentation now explains validation, evidence-based risk explanation, exports, graph filtering, and updated demo flow.

**Fixed**

- Prevented generated uploaded CSV files from being committed by adding `backend/data/uploaded_*.csv` to `.gitignore`.

**Why this supports the rubric**

- Improves Knowledge and Understanding by making the RDF/inference evidence path visible.
- Improves Innovation by showing explainable semantic risk investigation instead of only risk tables.
- Improves Software Clarity by separating validation, reasoning, graph/evidence output, and UI responsibilities.
- Improves Demonstration by giving clear tabs, exports, and graph filters for a short presentation.
- Supports Teamwork traceability by documenting the change and verification.

**Verification commands and results**

- `.\.venv\Scripts\python.exe -m compileall backend frontend` - passed.
- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider` - 25 passed.

**Known limitations**

- Validation is implemented as transparent Python checks, not formal SHACL shapes yet.
- Evidence views are designed for the compact demo graph; very large graphs would need pagination or search.
- Export support is lightweight and intended for report/demo evidence, not enterprise data pipelines.
