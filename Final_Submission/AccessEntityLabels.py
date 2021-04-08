'''
Created on 19 Jan 2021

@author: ejimenez-ruiz
'''
from owlready2 import *
from rdflib import Graph


def getClasses(onto):        
    return onto.classes()
    
def getDataProperties(onto):        
    return onto.data_properties()
    
def getObjectProperties(onto):        
    return onto.object_properties()
    
def getIndividuals(onto):    
    return onto.individuals()


def getRDFSLabelsForEntity(entity):
    #if hasattr(entity, "label"):
    return entity.label


def getRDFSLabelsForEntity(entity):
    #if hasattr(entity, "label"):
    return entity.label    


def loadOntology(urionto):
    
    #Method from owlready
    onto = get_ontology(urionto).load()
    
    print("Classes in Ontology: " + str(len(list(getClasses(onto)))))
    for cls in getClasses(onto):
        #Name of entity in URI. But in some cases it may be a 
        #code like in mouse and human anatomy ontologies                
        print(cls.iri)
        print("\t"+cls.name)  
        #Labels from RDFS label
        print("\t"+str(getRDFSLabelsForEntity(cls)))
        




#Load ontology from URI or local file
urionto="cmt.owl"
#urionto="ekaw.owl"
#urionto="confOf.owl"
#urionto="human.owl"
#urionto="mouse.owl"

# loadOntology(urionto)


