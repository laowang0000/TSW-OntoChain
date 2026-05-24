from rdflib.namespace import RDF, RDFS, OWL

from backend.services.ontology_service import OC, load_ontology


def test_ontology_loads_required_classes_and_properties():
    graph = load_ontology()

    assert (OC.Wallet, RDF.type, OWL.Class) in graph
    assert (OC.HighRiskWallet, RDFS.subClassOf, OC.Wallet) in graph
    assert (OC.SuspiciousTransaction, RDFS.subClassOf, OC.Transaction) in graph
    assert (OC.sentTo, RDF.type, OWL.ObjectProperty) in graph
    assert (OC.riskExplanation, RDF.type, OWL.DatatypeProperty) in graph
    assert (OC.riskExplanation, RDFS.range, None) in graph
