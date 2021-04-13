'''
Created on 01 April 2021
@author: zacharias.detorakis@city.ac.uk

Perform a basic alignment between the pizza.owl ontology and the created ontology.
This alignment is important to perform SPARQL queries using the vocabulary of the pizza.owl ontology instead of the created ontology.
'''
import sys
sys.path.append('./lib/')

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

class Task5Solution(object):

    def __init__(self):

        #Initialise a graph
        self.g = Graph()
        self.df_entity_scores = []
    
    def loadGraph(self,data_file):
        self.g.parse(data_file, format="ttl")

    def saveGraph(self, file_output):
        """
        A function used to save a graph to a turle file
        ...

        Attributes
        ----------
        file_output : string
            the name of the file that the KG will be saved as (extension included)
        """

        self.g.serialize(destination=file_output, format='ttl')
        print(f"{str(len(self.g))} triples saved in {file_output}.")
    
    def getClasses(self,onto):        
        return onto.classes()
        
    def getDataProperties(self,onto):        
        return onto.data_properties()
        
    def getObjectProperties(self,onto):        
        return onto.object_properties()
        
    def getIndividuals(self,onto):    
        return onto.individuals()

    def getRDFSLabelsForEntity(self,entity):
        #if hasattr(entity, "label"):
        return entity.label
    
    def extractEntities(self,urionto, entity_type = 'class'):
        
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
            print(f"Classes in {urionto} Ontology: {str(len(list(self.getClasses(onto))))}")
            entities = list(self.getClasses(onto))
        
        #...or the object properties
        elif entity_type == 'objectProperty':
            print(f"Object Properties in {urionto} Ontology: {str(len(list(self.getObjectProperties(onto))))}")
            entities = self.getObjectProperties(onto)
            
        #...or the data properties
        elif entity_type == 'dataProperty':
            print(f"Data Properties in {urionto} Ontology: {str(len(list(self.getDataProperties(onto))))}")
            entities = self.getDataProperties(onto)
        
        #...or the individuals from that ontology
        elif entity_type == 'individual':
            print(f"Individuals in {urionto} Ontology: {str(len(list(self.getIndividuals(onto))))}")
            entities = self.getIndividuals(onto)
        
        #else if the user input is not one of the valid entity types print an error message
        else:
            print("Incorrect entity type")

        #create a new array to hold all the extracted iris, their name and their label(s). Be it for classes, properties or individuals 
        entity_dict = []
        for entity in entities:
            temp = {}
            temp["iri"] = entity.iri
            temp["name"] = entity.name
            temp["labels"] = self.getRDFSLabelsForEntity(entity)
            entity_dict.append(temp)
            
            
        return entity_dict

    def compare2Arrays(self,array_1, array_2, entity_type, entity_scores, annotation = 'name'):
        
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

    def ontologyMatcher(self,uri1, uri2, annotation = 'name'):
        
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
        dict_uri1_classes = self.extractEntities(uri1,"class")
        dict_uri2_classes = self.extractEntities(uri2,"class")
        dict_uri1_obj_properties = self.extractEntities(uri1,"objectProperty")
        dict_uri2_obj_properties = self.extractEntities(uri2,"objectProperty")
        dict_uri1_data_properties = self.extractEntities(uri1,"dataProperty")
        dict_uri2_data_properties = self.extractEntities(uri2,"dataProperty")
        
        # Create an empty array to hold the objects. each object is a dictionary with two uris and the score of the similarity of their names
        entity_scores = []
        
        # compare class names and add the scores to the dictionary
        entity_scores = self.compare2Arrays(dict_uri1_classes, dict_uri2_classes, 'class', entity_scores, annotation)
        
        # ...do the same with object properties
        entity_scores = self.compare2Arrays(dict_uri1_obj_properties, dict_uri2_obj_properties, 'objectProperty', entity_scores, annotation)
        
        # ...do the same with data properties
        entity_scores = self.compare2Arrays(dict_uri1_data_properties, dict_uri2_data_properties, 'dataProperty', entity_scores, annotation)
        
        # finally we convert the dictionary to a dataframe to be able to filter pairs with the score above a certain threshold
        self.df_entity_scores = pd.DataFrame(entity_scores)

    def createAlignmentTripples(self,threshold=0.0):
        
        """
        A function create a graph with the tripples as specified int the entity scores list

        ...

        Attributes
        ----------
        threshold : float
            a number used to filter the pairs that have scored higher than the threshold and only consider them for the graph triples
        """
        self.g.bind("owl", OWL)
        self.g.bind("zdetor", Namespace("https://www.city.ac.uk/ds/inm713/zacharias_detorakis#"))
        self.g.bind("pizza", Namespace("http://www.co-ode.org/ontologies/pizza/pizza.owl#"))
        
        matched_onto2_entities = []

        # iterate throw the rows where the score is above a certain thresholf and create the relevant triples. the score table is sorted based on scores so the pair with the highest score appears first
        for index, row in self.df_entity_scores[self.df_entity_scores['score']>threshold].sort_values(by='score',ascending = False).iterrows():
            
            # we check if the entity from the second ontology has already been matched with a higher score and if it has we do not add the new pair in the graph 
            if row['entity2'] not in matched_onto2_entities:
                
                #we append the new entity from onto2 to the array so as do ignore it if it shows up again in lower scores
                matched_onto2_entities.append(row['entity2'])
                if row['entity_type'] == 'class':
                    self.g.add((URIRef(row['entity1']), OWL.equivalentClass, URIRef(row['entity2'])))
                elif row['entity_type'] == 'objectProperty':
                    self.g.add((URIRef(row['entity1']), OWL.equivalentProperty, URIRef(row['entity2'])))
                elif row['entity_type'] == 'dataProperty':
                    self.g.add((URIRef(row['entity1']), OWL.equivalentProperty, URIRef(row['entity2'])))
        # return g   

    def returnResults(self, query_string):
        """
        A function used to run the sparql query from the query_string on the KG g and return the results as a dataframe as well as the length of the results
        ...

        Attributes
        ----------
        query_string : string
            the string containing the SPARQL query
        """

        #Excecute the query
        qres = self.g.query(query_string)


        #parse the results and append them to a list of objects that will be converted to a dataframe
        results = []
        for row in qres:
            element = {}
            for key in row.labels.keys():
                element[key]= row[row.labels[key]]
            results.append(element)
        
        return len(qres), pd.DataFrame(results)    

if __name__ == '__main__':

    import argparse
    import configparser

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", type=str, default='default.cfg', help="Configuration file")
    parser.add_argument("--load_data", type=str, default=None, help="Whether to load the data for the reasoning")
    parser.add_argument("--perform_alignment", type=str, default=None, help="Whether to perform the ontology alignment")
    parser.add_argument("--kg_data", type=str, default=None, help="The ttl with the KG with the data loaded from the csv")
    parser.add_argument("--ref_owl", type=str, default=None, help="")
    parser.add_argument("--ref_ttl", type=str, default=None, help="")
    parser.add_argument("--cw_owl", type=str, default=None, help="")
    parser.add_argument("--cw_ttl", type=str, default=None, help="")
    parser.add_argument("--alignment_ttl", type=str, default=None, help="")

    FLAGS, unparsed = parser.parse_known_args()

    # # read and combine configurations
    # # overwrite the parameters in the configuration file by the command parameters
    config = configparser.ConfigParser()
    config.read(FLAGS.config_file)
    if FLAGS.load_data is not None:
        config['BASIC']['load_data'] = FLAGS.load_data
    if FLAGS.perform_alignment is not None:
        config['BASIC']['perform_alignment'] = FLAGS.perform_alignment
    if FLAGS.kg_data is not None:
        config['DOCUMENT']['kg_data'] = FLAGS.kg_data
    if FLAGS.ref_owl is not None:
        config['DOCUMENT']['ref_owl'] = FLAGS.ref_owl
    if FLAGS.ref_ttl is not None:
        config['DOCUMENT']['ref_ttl'] = FLAGS.ref_ttl
    if FLAGS.cw_owl is not None:
        config['DOCUMENT']['cw_owl'] = FLAGS.cw_owl
    if FLAGS.cw_ttl is not None:
        config['DOCUMENT']['cw_ttl'] = FLAGS.cw_ttl
    if FLAGS.alignment_ttl is not None:
        config['DOCUMENT']['alignment_ttl'] = FLAGS.alignment_ttl

    def str2bool(v):
        return v.lower() in ("yes", "true", "t", "1")

    load_kg_with_data = str2bool(config['BASIC']['load_data'])
    perform_alignment = str2bool(config['BASIC']['perform_alignment'])
    # #perform alignment
    # perform_alignment = False
    # # Load the KG with the csv data
    # load_kg_with_data = False

    solution = Task5Solution()

    


    #####################################
    #                                   #
    #           Subtask OA.1            #
    #                                   #
    #####################################
    '''
    Compute equivalences between the entities of the input ontologies. Save the equivalences as triples in turtle format (.ttl). 
    Tip: use owl:equivalentClass and owl:equivalentProperty as predicates of the equivalence triples
    '''
    
    if perform_alignment:
        reference_ontology_owl = config['DOCUMENT']['ref_owl']
        cw_ontology_owl = config['DOCUMENT']['cw_owl']
        alignment_output_filename = 'output_files/pizza-zdetor-alignment.ttl'
        threshold = 0.9

        # Use the matcher function to compare the two ontologies and load the results in a dataframe 'solution.df_entity_scores'
        solution.ontologyMatcher(reference_ontology_owl, cw_ontology_owl, 'name')
        # print(solution.df_entity_scores.head(5))

        # parse the dataframe with the scores and create the triples for those pairs of entities that scored above the threshold. Add the tripples to the KG
        solution.createAlignmentTripples(threshold)
        #print the resulting triples in a ttl file
        # print(solution.g.serialize(format="turtle").decode("utf-8"))
        solution.g.serialize(destination=alignment_output_filename, format='ttl')

    else:
        try:
            alignment_input_filename = config['DOCUMENT']['alignment_ttl']
            solution.loadGraph(alignment_input_filename)
            # print(solution.g.serialize(format="turtle").decode("utf-8"))
        except:
            print("Ontology alignment file not found!")

    print(f"Loaded {len(solution.g)} tripples from the ontology alignment")



    #####################################
    #                                   #
    #           Subtask OA.2            #
    #                                   #
    #####################################
    '''
    Perform reasoning with:
    (i) the created ontology, 
    (ii) the pizza.owl ontology and 
    (iii) the computed alignment (without the data) and list the number of unsatisfiable classes (i.e., classes that have the empty interpretation).
    '''

    # Load the created ontology
    cw_ontology_filename = config['DOCUMENT']['cw_ttl']
    solution.loadGraph(cw_ontology_filename)
    print(f"{len(solution.g)} tripples after loading the created ontology")

    # Load the reference pizza ontology
    ref_ontology_filename = config['DOCUMENT']['ref_ttl']
    solution.loadGraph(ref_ontology_filename)
    print(f"{len(solution.g)} tripples after loading the reference ontology")



    #####################################
    #                                   #
    #           Subtask OA.2a           #
    #                                   #
    #####################################
    filename = 'output_files/zdetor_pizza_alignment_unreasoned.ttl'
    solution.saveGraph(filename)

    

    #####################################
    #                                   #
    #           Subtask OA.2b           #
    #                                   #
    #####################################
    if load_kg_with_data:

        cw_kg_filename = config['DOCUMENT']['kg_data']
        solution.loadGraph(cw_kg_filename)
        print(f"{len(solution.g)} tripples after loading the KG data")

        query ="""
        SELECT ?pizzaName ?pizzaDescription
        WHERE{
                ?pizza  a pizza:MeatyPizza;
                        zdetor:name ?pizzaName;
                        zdetor:description ?pizzaDescription .
        }
        """



    ##
    print("Performing the reasoning")
    start = time.time()
    #perform the reasoning  with the created ontology and save to a new KG in ttl format
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(solution.g)
    print(f"Triples after OWL 2 RL reasoning: {len(solution.g)}.")

    end = time.time()
    print(f"Processing time {round((end-start)/60,2)} min")

    filename = 'output_files/zdetor_pizza_alignment_data_reasoned.ttl'
    solution.saveGraph(filename)

    # check for meaty pizzas 
    if load_kg_with_data:
        query ="""
        SELECT ?pizzaName ?pizzaDescription
        WHERE{
                ?pizza  a pizza:MeatyPizza;
                        zdetor:name ?pizzaName;
                        zdetor:description ?pizzaDescription .
        }
            """
        res_len, results = solution.returnResults(query)
        print(f"Pizzas with type pizza:MeatyPizza: {res_len}.")
        if res_len>0:
            print("Sample ressults:")
            print(results)