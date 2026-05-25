# SPARQL Examples

These queries can be pasted into the Streamlit SPARQL box or sent to `POST /query-sparql`. They are designed to demonstrate that SPARQL can query raw CSV-derived facts, ontology classes, and inferred risk facts from the same RDF graph.

## Why These Queries Matter

- They show **source facts**, such as wallet transfers and contract interactions.
- They show **inferred facts**, such as high-risk wallets and suspicious transactions.
- They show **ontology usage**, such as which OWL classes have instances.
- They support **evidence-based explanation**, where a selected entity's source and inferred facts can be verified.
- They help answer marking questions about RDF, RDFS, OWL, SPARQL, and inference.

## High-Risk Wallets With Explanations

Semantic question: Which wallets were inferred as high risk, and which rule explains each classification?

Expected demo result: rows for wallets such as `0xAlice` and `0xBob`, with risk score and explanation.

```sparql
SELECT DISTINCT ?wallet ?label ?score ?explanation
WHERE {
  ?wallet a oc:HighRiskWallet ;
          rdfs:label ?label ;
          oc:riskScore ?score ;
          oc:riskExplanation ?explanation .
}
ORDER BY DESC(?score)
```

## Suspicious Transactions With Explanations

Semantic question: Which transactions were inferred as suspicious, what amount caused the risk, and what rule explains it?

Expected demo result: high-value transactions above 10000, including explanation text.

```sparql
SELECT DISTINCT ?tx ?hash ?amount ?contract ?explanation
WHERE {
  ?tx a oc:SuspiciousTransaction ;
      oc:transactionHash ?hash ;
      oc:amount ?amount ;
      oc:interactsWithContract ?contract ;
      oc:riskExplanation ?explanation .
}
ORDER BY DESC(?amount)
```

## Wallet-To-Wallet Transfers

Semantic question: Which wallet resources are connected by the `oc:sentTo` object property?

Expected demo result: sender and receiver wallet labels, such as `0xAlice` to `0xMixerOne`.

```sparql
SELECT DISTINCT ?sender ?senderLabel ?receiver ?receiverLabel
WHERE {
  ?sender oc:sentTo ?receiver ;
          rdfs:label ?senderLabel .
  ?receiver rdfs:label ?receiverLabel .
}
ORDER BY ?senderLabel ?receiverLabel
```

## Smart Contract Interactions

Semantic question: Which transaction resources interact with which smart contract resources?

Expected demo result: transaction hashes linked to contract labels such as `0xRiskyContract`.

```sparql
SELECT DISTINCT ?tx ?hash ?amount ?contract ?contractLabel
WHERE {
  ?tx a oc:Transaction ;
      oc:transactionHash ?hash ;
      oc:amount ?amount ;
      oc:interactsWithContract ?contract .
  ?contract rdfs:label ?contractLabel .
}
ORDER BY ?contractLabel DESC(?amount)
```

## All Inferred Facts

Semantic question: Which RDF facts were added by reasoning for risk classification and explanation?

Expected demo result: inferred class, risk score, risk explanation, risk indicator, and fraud pattern facts.

```sparql
SELECT DISTINCT ?entity ?entityLabel ?inferredClass ?predicate ?object
WHERE {
  VALUES ?inferredClass { oc:HighRiskWallet oc:SuspiciousTransaction oc:SuspiciousContract }
  VALUES ?predicate { oc:riskScore oc:riskExplanation oc:hasRiskIndicator oc:classifiedAs }
  ?entity a ?inferredClass ;
          rdfs:label ?entityLabel .
  ?entity ?predicate ?object .
}
ORDER BY ?inferredClass ?entityLabel ?predicate
```

## Ontology Classes Used In Graph

Semantic question: Which OWL ontology classes have instances in the generated knowledge graph?

Expected demo result: ontology classes such as `oc:Wallet`, `oc:Transaction`, `oc:HighRiskWallet`, and `oc:SuspiciousTransaction` with instance counts.

```sparql
SELECT DISTINCT ?class ?classLabel (COUNT(DISTINCT ?entity) AS ?entityCount)
WHERE {
  ?entity a ?class .
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?classLabel . }
}
GROUP BY ?class ?classLabel
ORDER BY ?class
```

## Mixer Exposure Relationships

Semantic question: Which wallet-to-wallet transfers involve a wallet identified as a mixer?

Expected demo result: wallets that transferred to mixer wallets.

```sparql
SELECT DISTINCT ?wallet ?walletLabel ?mixer ?mixerLabel
WHERE {
  ?wallet oc:sentTo ?mixer ;
          rdfs:label ?walletLabel .
  ?mixer a oc:MixerWallet ;
         rdfs:label ?mixerLabel .
}
```

## Evidence Query For One Risk Entity

Semantic question: Which inferred risk facts explain a selected entity?

Expected demo result: for `0xAlice`, the query returns inferred type, risk score, risk explanation, risk indicator, and fraud pattern.

```sparql
SELECT ?predicate ?object
WHERE {
  oc:wallet_0xAlice ?predicate ?object .
  VALUES ?predicate { rdf:type oc:riskScore oc:riskExplanation oc:hasRiskIndicator oc:classifiedAs }
}
ORDER BY ?predicate ?object
```

## Source Evidence For A Wallet

Semantic question: Which source graph relationships show that a wallet interacted with another wallet before inference?

Expected demo result: source relationships for `0xAlice`, including interaction with `0xMixerOne`.

```sparql
SELECT ?wallet ?walletLabel ?predicate ?otherWallet ?otherLabel
WHERE {
  VALUES ?wallet { oc:wallet_0xAlice }
  VALUES ?predicate { oc:sentTo oc:receivedFrom }
  ?wallet ?predicate ?otherWallet ;
          rdfs:label ?walletLabel .
  ?otherWallet rdfs:label ?otherLabel .
}
ORDER BY ?predicate ?otherLabel
```
