from owlready2 import *
import pandas as pd
from rdflib import Graph, URIRef, BNode, Literal, Namespace
import AccessEntityLabels
import Levenshtein as lev
from stringcmp import isub
from rdflib.namespace import OWL
from CompareWithReference import compareWithReference
import time
import owlrl

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
 
def extractEntities(urionto, entity_type = 'class'):
    
    """
    A function used to extract the information from a given ontology. The returned objects is an array of dictionaries, each having the 'iri', 'name' and 'labels' keys

    ...

    Attributes
    ----------
    urionto : str
        the owl file containing the ontology (e.g. 'cmt.owl')
    entity_type : str
        the type of entity to extract from the ontology. The valid values are {'class', 'objectProperty', 'dataProperty', 'individual'}. if not specified the default is 'class'

    """
    
    #Method from owlready
    onto = get_ontology(urionto).load()
    
    entities = list([])
    
    #load the classes
    if entity_type == 'class':
        print(f"Classes in {urionto} Ontology: {str(len(list(getClasses(onto))))}")
        entities = list(getClasses(onto))
    
    #...or the object properties
    elif entity_type == 'objectProperty':
        print(f"Object Properties in {urionto} Ontology: {str(len(list(getObjectProperties(onto))))}")
        entities = getObjectProperties(onto)
        
    #...or the data properties
    elif entity_type == 'dataProperty':
        print(f"Data Properties in {urionto} Ontology: {str(len(list(getDataProperties(onto))))}")
        entities = getDataProperties(onto)
    
    #...or the individuals from that ontology
    elif entity_type == 'individual':
        print(f"Individuals in {urionto} Ontology: {str(len(list(getIndividuals(onto))))}")
        entities = getIndividuals(onto)
    
    #else if the user input is not one of the valid entity types print an error message
    else:
        print("Incorrect entity type")

    #create a new array to hold all the extracted iris, their name and their label(s). Be it for classes, properties or individuals 
    entity_dict = []
    for entity in entities:
        temp = {}
        temp["iri"] = entity.iri
        temp["name"] = entity.name
        temp["labels"] = getRDFSLabelsForEntity(entity)
        entity_dict.append(temp)
        
        
    return entity_dict

def compare2Arrays(array_1, array_2, entity_type, entity_scores, annotation = 'name'):
    
    """
    A function used to compare 2 lists (of ontology entities) and return an third list with entity pairs and they score and their type based on the lexical comparison using the isub metric

    ...

    Attributes
    ----------
    array_1 : list
        the first list containing entities from the first ontology to compare
    array_2 : list
        the second list containing entities from the second ontology to compare
    entity_type : str
        the type of entity to extract from the ontology. The valid values are {'class', 'objectProperty', 'dataProperty', 'individual'}. if not specified the default is 'class'
    entity_scores : list
        a list containing a pair of IRIs, their entity type and the score based on the selected distance. This list will become the output as well after enriched with the new pairs
    annotation: string
        the "attribute" to be used for the lexical comparison. The valid values are {'name', 'labels'}. If not specified the default value is 'name'

    """
    iterator = 0
    start = time.time()
    for i in array_1:
        iterator += 1
        score = 0
        best_pair = {}

        for j in array_2:
            
            #this part checks if we are comparing the names or the labels. that's because names are strings but labels are arrays so we need to get one level deeper
            if annotation == 'name':
                string1 = i[annotation]
                string2 = j[annotation]
            if annotation == 'labels':
                if (len(i[annotation])>0) & (len(j[annotation])>0):
                    string1 = i[annotation][0]
                    string2 = j[annotation][0]
                else:
                    string1 = ''
                    string2 = ''
            
            #only to this if both strings are not empty
            if (len(string1)>0) & (len(string2)>0):
                new_score = isub(string1,string2)
                if new_score > score:
                    score = new_score
                    best_pair = {"entity1": i['iri'], "entity2": j['iri'], "entity_type": entity_type, "score": score}
                    
        entity_scores.append(best_pair)

    end = time.time()


    #return the scores list
    return entity_scores

def ontologyMatcher(uri1, uri2, annotation = 'name'):
    
    """
    A function used to orchestrate the matching of two ontologies uri1 and uri2 by comparing the lexical similarity of all entities (i.e. classes and properties) based on the annotation (i.e. name or labels)

    ...

    Attributes
    ----------
    uri1 : string
        the name of the owl file of the first ontology to compare
    uri2 : string
        the name of the owl file of the second ontology to compare
    annotation: string
        the "attribute" to be used for the lexical comparison. The valid values are {'name', 'labels'}. If not specified the default value is 'name'

    """
    
    # load the classes and objects from the 2 uris in the respective arrays of objects
    dict_uri1_classes = extractEntities(uri1,"class")
    dict_uri2_classes = extractEntities(uri2,"class")
    dict_uri1_obj_properties = extractEntities(uri1,"objectProperty")
    dict_uri2_obj_properties = extractEntities(uri2,"objectProperty")
    dict_uri1_data_properties = extractEntities(uri1,"dataProperty")
    dict_uri2_data_properties = extractEntities(uri2,"dataProperty")
    
    # Create an empty array to hold the objects. each object is a dictionary with two uris and the score of the similarity of their names
    entity_scores = []
    
    # compare class names and add the scores to the dictionary
    entity_scores = compare2Arrays(dict_uri1_classes, dict_uri2_classes, 'class', entity_scores, annotation)
    
    # ...do the same with object properties
    entity_scores = compare2Arrays(dict_uri1_obj_properties, dict_uri2_obj_properties, 'objectProperty', entity_scores, annotation)
    
    # ...do the same with data properties
    entity_scores = compare2Arrays(dict_uri1_data_properties, dict_uri2_data_properties, 'dataProperty', entity_scores, annotation)
    
    # finally we convert the dictionary to a dataframe to be able to filter pairs with the score above a certain threshold
    return pd.DataFrame(entity_scores)

def createAlignmentTripples(enity_scores,threshold=0.0):
    
    """
    A function create a graph with the tripples as specified int the entity scores list

    ...

    Attributes
    ----------
    entity_scores : list
        a list containing a pair of IRIs, their entity type and the score based on the selected distance.
    threshold : float
        a number used to filter the pairs that have scored higher than the threshold and only consider them for the graph triples
    """
        
    #initialise a new graph
    g = Graph()

    g.bind("owl", OWL)
    g.bind("zdetor", Namespace("https://www.city.ac.uk/ds/inm713/zacharias_detorakis#"))
    g.bind("pizza", Namespace("http://www.co-ode.org/ontologies/pizza/pizza.owl#"))
    
    matched_onto2_entities = []

    # iterate throw the rows where the score is above a certain thresholf and create the relevant triples. the score table is sorted based on scores so the pair with the highest score appears first
    for index, row in df_entity_scores[df_entity_scores['score']>threshold].sort_values(by='score',ascending = False).iterrows():
        
        # we check if the entity from the second ontology has already been matched with a higher score and if it has we do not add the new pair in the graph 
        if row['entity2'] not in matched_onto2_entities:
            
            #we append the new entity from onto2 to the array so as do ignore it if it shows up again in lower scores
            matched_onto2_entities.append(row['entity2'])
            if row['entity_type'] == 'class':
                g.add((URIRef(row['entity1']), OWL.equivalentClass, URIRef(row['entity2'])))
            elif row['entity_type'] == 'objectProperty':
                g.add((URIRef(row['entity1']), OWL.equivalentProperty, URIRef(row['entity2'])))
            elif row['entity_type'] == 'dataProperty':
                g.add((URIRef(row['entity1']), OWL.equivalentProperty, URIRef(row['entity2'])))
    return g


# Use the matcher function to compare the two ontologies and load the results in a dataframe
df_entity_scores = ontologyMatcher('pizza.owl', 'zdetor.owl', 'name')
filename = 'pizza-zdetor-alignment-o.ttl'

threshold = 0.9


# display(df_entity_scores[df_entity_scores['score']>threshold].sort_values(by='score',ascending = False))


# parse the dataframe with the scores and creates the triples for those pairs of entities that scored above the threshold. Add the tripples to the KG
g = createAlignmentTripples(df_entity_scores,threshold)
#print the resulting triples in a ttl file
print(g.serialize(format="turtle").decode("utf-8"))
# g.serialize(destination=filename, format='ttl')



#Initialise a graph
g = Graph()

# Load the asserted tripples from the KG
g.parse("cw-data.ttl", format="ttl")
print("Loaded '" + str(len(g)) + "' triples.")

g.parse("zdetor.ttl", format="ttl")
print("Loaded '" + str(len(g)) + "' triples.")

g.parse("pizza.ttl", format="ttl")
print("Loaded '" + str(len(g)) + "' triples.")

g.parse("pizza-zdetor-alignment.ttl", format="ttl")
print("Loaded '" + str(len(g)) + "' triples.")

start = time.time()
#perform the reasoning  with the created ontology and save to a new KG in ttl format
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(g)
print("Triples after OWL 2 RL reasoning: '" + str(len(g)) + "'.")

end = time.time()
print(f"Processing time {round((end-start)/60,2)} min")

filename = 'final_temp.ttl'
g.serialize(destination=filename, format='ttl')