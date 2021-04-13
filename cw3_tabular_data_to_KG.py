'''
Created on 01 April 2021
@author: zacharias.detorakis@city.ac.uk

Transform Pizza_data into RDF triples using your favourite programming language.
Please document your code. Save the RDF data into turtle format (.ttl).
'''

# Import Libraries
import sys
sys.path.append('./lib/')


from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from rdflib.namespace import OWL, RDF, RDFS, FOAF, XSD
import pandas as pd
import math
from SPARQLWrapper import SPARQLWrapper, JSON
from stringcmp import isub
from lookup import DBpediaLookup
import time
# import yake
import re

import owlrl

class FinalCoursework(object):
    """
    This will contain the solution for the coursework for the SW&KGT
    """
    
    def __init__(self, input_csv):
        
        # The file containing the data to load in the KG
        self.file = input_csv
        
        #Intialise the KG
        self.g = Graph()
        
        #setup the ontology IRI used for the courseworkontology..
        self.zdetor_ns_str= "https://www.city.ac.uk/ds/inm713/zacharias_detorakis#"
        #Special namspaces class to create directly URIRefs in python.           
        self.zdetor = Namespace(self.zdetor_ns_str)
        #Prefixes for the serialization
        self.g.bind("zdetor", self.zdetor)
        
        self.classStringToURI = dict()
        
        
        #read the raw data into a dataframe
        self.df = pd.read_csv(filepath_or_buffer = self.file, sep=',', quotechar='"',escapechar="\\")
    
    def is_nan(self, x):
        return (x != x)

    def findNewRestaurantName(self,original_value,mapping_dict):
        """
        A function used to map a given value to a new one as defined in the mapping dictionary
        ...

        Attributes
        ----------
        original_value : str
            the original value to be mapped. In this case this will be the concatenated field (name+address)
        mapping_dict : dict
            this is a dictionary where the 'key' is the original value and the 'value' is the new value it maps to
        """
        try:
            return mapping_dict[original_value]
        except:
            return 'invalid'

    def createNewRestaurantNames(self):
        """
        A function used to create a new name for restaurants that share the same name but based on the addresses seem to be different. The new name will be created as a new 'restaurant_name' column in the df 
        ...

        Attributes
        ----------
        original_df : dataframe
            the original dataframe to be updated with the new_name column
        """
        
        # group the restaurant by name and filter out any restaurant with exactly one address
        df_group = pd.DataFrame(self.df.groupby('name')['address'].nunique())
        df_dup_restaurants = df_group[df_group.address>1]

        # next we create a new version of the df to add the new name column
        new_df = self.df
        # for now populate the column with a concatenation of name and address
        new_df['restaurant_name']=new_df.apply(lambda x:'%s_%s' % (x['name'],x['address']),axis=1)

        # next we create a termporary dataframe to store the name and concatenated column. drop the duplicates (from the multiple menu items) and sort the df
        temp = new_df[['name', 'restaurant_name']].drop_duplicates()
        temp.sort_values(by='name',inplace=True)

        # finally create a dictionary mappin the concatenated field to a new restaurant name by 
        # - adding a sequence number at the end of the duplicates or 
        # - reusing the existing name for restaurants that appear only once
        prev_name = ''
        incr = 1
        new_name_dict = {}
        for index, row in temp.iterrows():
            if row['name'] == prev_name:
                incr += 1
            else:
                incr = 1

            if row['name'] in str(df_dup_restaurants.index):
                new_name_dict[row['restaurant_name']]= row['name'] + '___' + str(incr)
                prev_name = row['name']
            else:
                new_name_dict[row['restaurant_name']]= row['name']

        # Finally apply the function to map the concatenated field to the new name
        new_df['restaurant_name'] = new_df['restaurant_name'].apply(lambda x: self.findNewRestaurantName(x,new_name_dict))
        # new_df.to_csv("temp.csv")
        self.df = new_df

    def convertPostCodeStringToPostCodes(self,post_code):

        #create a new empty list for the post codes
        post_code_list = []
        
        #separate the post codes by commas first
        separate_val = re.split(r'[,( ]\s*', post_code.replace("- ", "-").replace("– ","–")) 
        for val in separate_val:

            #the within each value we check if we have a range
            if ((val.find('–')>0) or (val.find('-')>0)) :
                pc_range = re.split(r'[-–]\s*', val)

                #if we do have a range then we create all the post codes in that range and append them to the list
                try:
                    for pc in range(int(pc_range[0]),int(pc_range[1])+1):
                    #we append the post codes as strings and if need be we add leading zeros to make the string 5 characters long
                        post_code_list.append(str(pc).zfill(5))
                except:
                    pass
                        
            else:
                try:
                    int(val)
                    post_code_list.append(val)
                except:
                    pass
        return post_code_list

    def createPostCode2StateMap(self):
        
        
        #first we create a list of all the post codes and the cities from DBpedia
        endpoint_url = "http://dbpedia.org/sparql"

        sparqlw = SPARQLWrapper(endpoint_url)
        sparqlw.setReturnFormat(JSON)

        query = """
        SELECT ?city ?state str(?cityName) ?iso2StateCode ?postCode
        WHERE {
            ?state  dct:subject dbc:States_of_the_United_States;
                    dbo:postalCode ?iso2StateCode.
            ?city   a dbo:City;
                    dbo:subdivision ?state;
                    rdfs:label ?cityName;
                    dbo:postalCode ?postCode.

        FILTER (?iso2StateCode != "").
        FILTER langMatches( lang(?cityName), "en" )
        }
        """
        sparqlw.setQuery(query)
        results = sparqlw.query().convert()
        
        #next we create a temporary dictionary with the post code string and the state code. However the post code in this dictionary is sometimes a range or a combination of post codes and ranges
        temp_post_dict = dict()
        for i in results['results']['bindings']:
            temp_post_dict[i['postCode']['value']] = i['iso2StateCode']['value']
        
        # Finally we reprocess the temp_post_dict post codes so we have extract all the post codes from the ranges and still map them to the same state
        postcode_to_state = dict()
        for post_code in temp_post_dict.keys():
            for pc in self.convertPostCodeStringToPostCodes(post_code):
                postcode_to_state[pc] = temp_post_dict[post_code]
        
        
        # next we create a dictionary with cities and states        
        city_to_state = dict()
        for row in results['results']['bindings']:
            city_to_state[row['callret-2']['value']] = row['iso2StateCode']['value']
        
        return postcode_to_state, city_to_state

    def findStateByPostCodeCity(self,postcode, city, postcode_to_state, city_to_state):
        """
        A function used to map a given post code or city in the US to the respective state. Exact matches are expected instead of lexical similarity
        ...

        Attributes
        ----------
        postcode : str
            the post code to be mapped
        city : str
            the city to be mapped. Unlike the post code the city can be matched if it exists as a substring in the dictionary
        """
        
        try:
            return postcode_to_state[postcode]
        except:
            try:
                lst = [value for key, value in city_to_state.items() if city.lower() in key.lower()]
                return max(set(lst), key=lst.count)
            except:
                pass

    def getExternalKGURI(self,name):
        '''
        Approximate solution: We get the entity with highest lexical similarity
        The use of context may be necessary in some cases        
        '''
        
        dbpedia = DBpediaLookup()
        entities = dbpedia.getKGEntities(name, 5)
        #print("Entities from DBPedia:")
        current_sim = -1
        current_uri=''
        for ent in entities:           
            isub_score = isub(name, ent.label) 
            if current_sim < isub_score:
                current_uri = ent.ident
                current_sim = isub_score

  
        return current_uri

    def loadStateISO2UrisFromDBPedia(self):
        endpoint_url = "http://dbpedia.org/sparql"

        sparqlw = SPARQLWrapper(endpoint_url)
        sparqlw.setReturnFormat(JSON)
        
        #Create the sparql query to get the URIs for the states from the iso2 state code
        state_iso2_query = """
        SELECT ?state ?iso2StateCode
        WHERE {
            ?state  dct:subject dbc:States_of_the_United_States;
                    dbo:postalCode ?iso2StateCode.
        FILTER (?iso2StateCode != "").
        }
        """
        
        sparqlw.setQuery(state_iso2_query)
        state_results = sparqlw.query().convert()

        # create a new key for the states and...
        self.classStringToURI['state_code'] = dict()

        # the the code to URI mappings
        for state in state_results['results']['bindings']:
            self.classStringToURI['state_code'][state['iso2StateCode']['value'].lower()] = state['state']['value']

    def mappingToCreateTypeTriple(self, subject_column, class_type, use_external_uri):
        
        # First we create a new key for the class with a value of another dictionary
        if subject_column != 'state_code':
            self.classStringToURI[subject_column] = dict()

        # Then we iterate through the rows in the subject column and either reuse an existing URI of contruct it from scratch
        for subject in self.df[subject_column]:
            
            #We use the subject_column value to create the fresh URI if this if the first time we see that value. 
            # If we've seen the value before we do not do anything since we've already added the tripple to the graph
            #################################### CHECK FOR NULL VALUES
            try:
                if subject.lower() not in self.classStringToURI[subject_column]:
                    if use_external_uri:
                        entity_uri =  self.getExternalKGURI(subject.lower())
                    else:
                        entity_uri = self.zdetor_ns_str + subject.lower().replace(" ", "_").replace("'","_").replace("(","_").replace(")","_").replace("&","_").replace("|","_")
                    self.classStringToURI[subject_column][subject.lower()] = entity_uri
                else:
                    entity_uri = self.classStringToURI[subject_column][subject.lower()]
                    
                #Add the tripple to the KG
                self.g.add((URIRef(entity_uri), RDF.type, class_type))
            except:
                pass
          
    def mappingToCreateLiteralTriple(self, subject_column, object_column, predicate, datatype):

        for subject, lit_value in zip(self.df[subject_column], self.df[object_column]):

            # check if the value is empty and if it is do not create the litteral value
            if self.is_nan(lit_value) or lit_value==None or lit_value=="":
                pass

            else:
                try:
                    #Uri as already created
                    entity_uri=self.classStringToURI[subject_column][subject.lower()]

                    #Literal
                    lit = Literal(lit_value, datatype=datatype)

                    #New triple
                    self.g.add((URIRef(entity_uri), predicate, lit))
                except:
                    pass

    def mappingToCreateObjectTriple(self, subject_column, object_column, predicate):

        for subject, object in zip(self.df[subject_column], self.df[object_column]):


            if self.is_nan(object) or object==None or object=="":
                pass

            else:
                #Uri as already created
                subject_uri=self.classStringToURI[subject_column][subject.lower()]
                object_uri=self.classStringToURI[object_column][object.lower()]

                #New triple
                self.g.add((URIRef(subject_uri), predicate, URIRef(object_uri)))

    def getClasses(self,onto):        
            return onto.classes()
        
    def getOntoClassesByTerm(self,urionto, prefix, parent_class):

        # load the ontology
        onto = get_ontology(urionto).load()
        
        # get all ontology classes
        entities = list(self.getClasses(onto))

        
        #create a dictionary with subclasses of the parent_class. Assuming the name of the parent class is there as a suffix in the subclass
        classes = dict()
        for entity in entities:
            #expectein the name of the parent class to appear in the subclass name but NOT immediately after the prefix
            if str(entity).find(parent_class)>len(prefix)+1:
                classes[str(entity).replace(prefix+".","").replace(parent_class,"").lower()] = str(entity).replace('zdetor.',solution.zdetor_ns_str)
        return classes

    def mappingToCreateObjectProperty(self, subject_column, object_column, object_dict, predicate = RDF.type):

        for subject, object in zip(self.df[subject_column], self.df[object_column]):

            if self.is_nan(object) or object==None or object=="":
                pass

            else:
                separate_val = set(re.split(r'[,( ]\s*', object.lower()))

                for val in separate_val:
                    try:

                        subject_uri=self.classStringToURI[subject_column][subject.lower()]
                        self.g.add((URIRef(subject_uri), predicate, URIRef(object_dict[val])))
                    except:
                        pass
                    
    def mappingToCreatePizzaToppings(self, subject_column, object_column, object_dict, predicate = RDF.type):

        for subject, object in zip(self.df[subject_column], self.df[object_column]):

            if self.is_nan(object) or object==None or object=="":
                pass

            else:
                separate_val = set(re.split(r'[.,( ]\s*', object.lower()))

                for val in separate_val:
                    try:
                        subject_uri=self.classStringToURI[subject_column][subject.lower()]
                        self.g.add((URIRef(subject_uri), predicate, URIRef(object_dict[val])))
                    except:
                        pass

    def saveGraph(self, file_output):

        self.g.serialize(destination=file_output, format='ttl')
        print("Triples including ontology: '" + str(len(self.g)) + "'.")

    def performReasoning(self, ontology_file):

        print("Triples including ontology: '" + str(len(self.g)) + "'.")
        
        #We should load the ontology first
        self.g.load(ontology_file,  format='ttl') #e.g., format=ttl


        #We apply reasoning and expand the graph with new triples 
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(sellf.g)

        print("Triples after OWL 2 RL reasoning: '" + str(len(self.g)) + "'.")

if __name__ == '__main__':
    input_csv = "./input_files/INM713_coursework_data_pizza_8358_1_reduced.csv"
    # input_csv = "./input_files/INM713_coursework_data_pizza_8358_1_reduced - small.csv"
    
    solution = FinalCoursework(input_csv)

    ############################################################
    #                                                          #
    #                   DATA PRE - PROCESSING                  #
    #                                                          #
    ############################################################

    #Add a new column to make restaurant name unique per address
    solution.createNewRestaurantNames()
    print("'restaurant_name' column added")

    #Add a new state_code column with cleaner codes for the states
    postcode_to_state, city_to_state = solution.createPostCode2StateMap()
    solution.df['state_code'] = solution.df.apply(lambda x: x.state if len(x.state)==2 else solution.findStateByPostCodeCity(x.postcode,x.city, postcode_to_state, city_to_state),axis=1)
    print("'state_code' column added")

    #We need to add one more column to the dataframe by concatenating the address column with the state column 
    # in order to generate unique values to use for the generation of the address class URI
    solution.df['address_id'] = solution.df.apply(lambda x: x.state+'_'+x.address,axis=1)
    print("'address_id' column added")

    #We need to add one more column to the dataframe by concatenating the menu item and the restaurant name in order to create 
    # a unique URI for pizzas that are served at different restaurants (i.e. if a pizza is served at 2 different restaurants has the same name we need to create to instances instead of one)
    solution.df['pizza_name'] = solution.df.apply(lambda x: x.restaurant_name+'_'+str(x['menu item']),axis=1)
    print("'pizza_name' column added")

    #####################################################
    #                                                   #
    #                   TRIPLE CREATION                 #
    #                                                   #
    #####################################################

    ################################
    #                              #
    #           CLASSES            #
    #                              #
    ################################ 
    print('CREATING CLASSES:')
    print('* Processing restaurant class', end='')
    start = time.time()
    if 'restaurant_name' in solution.df:
        solution.mappingToCreateTypeTriple('restaurant_name',solution.zdetor.Restaurant, False)
    end = time.time()
    print(f" - COMPLETED ({round(end-start,2)} sec)")

    start = time.time()
    print('* Processing city class', end='')
    solution.g.bind("dpo", Namespace("http://dbpedia.org/resource/"))
    if 'city' in solution.df:
        solution.mappingToCreateTypeTriple('city',solution.zdetor.City, True)
    end = time.time()
    print(f" - COMPLETED ({round(end-start,2)} sec)")
    
    start = time.time()
    print('* Processing country class', end='')  
    if 'country' in solution.df:
        solution.mappingToCreateTypeTriple('country',solution.zdetor.Country, True)
    end = time.time()
    print(f" - COMPLETED ({round(end-start,2)} sec)")
    
    start = time.time()
    print('* Processing state class', end='')
    solution.loadStateISO2UrisFromDBPedia()
    if 'state_code' in solution.df:
        solution.mappingToCreateTypeTriple('state_code',solution.zdetor.State, True)
    end = time.time()
    print(f" - COMPLETED ({round(end-start,2)} sec)")
    
    start = time.time()
    print('* Processing address class', end='')    
    if 'address_id' in solution.df:
        solution.mappingToCreateTypeTriple('address_id',solution.zdetor.Address, False)
    end = time.time()
    print(f" - COMPLETED ({round(end-start,2)} sec)")
    
    start = time.time()
    print('* Processing pizza and menu item classes', end='')
    if 'pizza_name' in solution.df:
        solution.mappingToCreateTypeTriple('pizza_name',solution.zdetor.Pizza, False)
        solution.mappingToCreateTypeTriple('pizza_name',solution.zdetor.MenuItem, False)
    end = time.time()
    print(f" - COMPLETED ({round(end-start,2)} sec)")
    
    start = time.time()
    print('* Processing currency class')
    if 'currency' in solution.df:
        solution.mappingToCreateTypeTriple('currency',solution.zdetor.Currency, False)

    #########################################
    #                                       #
    #           OBJECT PROPERTIES           #
    #                                       #
    ######################################### 
    print('CREATING OBJECT PROPERTIES:')

    if 'name' in solution.df:
        solution.mappingToCreateObjectTriple('restaurant_name','address_id',solution.zdetor.hasAddress)
        if 'pizza_name' in solution.df:
            solution.mappingToCreateObjectTriple('restaurant_name','pizza_name',solution.zdetor.hasMenuItem)

    if 'address_id' in solution.df:
        solution.mappingToCreateObjectTriple('address_id','city',solution.zdetor.hasCity)
        solution.mappingToCreateObjectTriple('address_id','state_code',solution.zdetor.hasState)
        solution.mappingToCreateObjectTriple('address_id','country',solution.zdetor.hasCountry)
        
    if 'pizza_name' in solution.df:
        solution.mappingToCreateObjectTriple('pizza_name','currency',solution.zdetor.hasCurrency)

    #######################################
    #                                     #
    #           DATA PROPERTIES           #
    #                                     #
    ####################################### 
    if 'name' in solution.df:
        solution.mappingToCreateLiteralTriple('restaurant_name','name',solution.zdetor.name, XSD.string)
        
    if 'city' in solution.df:
        solution.mappingToCreateLiteralTriple('city','city',solution.zdetor.name, XSD.string)
    print('Cities complete')
        
    if 'country' in solution.df:
        solution.mappingToCreateLiteralTriple('country','country',solution.zdetor.name, XSD.string)
    print('Countries complete')

    if 'state_code' in solution.df:
        solution.mappingToCreateLiteralTriple('state_code','state_code',solution.zdetor.name, XSD.string)
    print('States complete')
        
    if 'address_id' in solution.df:
        solution.mappingToCreateLiteralTriple('address_id','address',solution.zdetor.addressLine, XSD.string)
        solution.mappingToCreateLiteralTriple('address_id','postcode',solution.zdetor.postCode, XSD.string)
        
    if 'pizza_name' in solution.df:
        solution.mappingToCreateLiteralTriple('pizza_name','item value',solution.zdetor.price, XSD.float)
        solution.mappingToCreateLiteralTriple('pizza_name','currency',solution.zdetor.currency, XSD.string)
        solution.mappingToCreateLiteralTriple('pizza_name','menu item',solution.zdetor.name, XSD.string)
        solution.mappingToCreateLiteralTriple('pizza_name','item description',solution.zdetor.description, XSD.string)

    from owlready2 import *
    
    #next we load the subClasses for the Restaurants, Pizzas and PizzaToppings from the ontology to use them in the tripples
    categories = solution.getOntoClassesByTerm('./input_files/zdetor.owl','zdetor','Restaurant')
    pizzas = solution.getOntoClassesByTerm('./input_files/zdetor.owl','zdetor','Pizza')
    toppings = solution.getOntoClassesByTerm('./input_files/zdetor.owl','zdetor','Topping')

    #we then create individuals for all the toppings (i.e. one individual per pizzaTopping class)
    solution.classStringToURI['topping'] = dict()
    for topping in toppings:

        entity_uri = solution.zdetor_ns_str+topping
        solution.classStringToURI['topping'][topping] = entity_uri
        solution.g.add((URIRef(entity_uri), RDF.type, URIRef(toppings[topping])))


    #finally we add the subclasses to the restaurants and pizzas
    solution.mappingToCreateObjectProperty('restaurant_name','categories',categories)
    solution.mappingToCreateObjectProperty('pizza_name','menu item',pizzas)

    # and the pizza topping URIs to the pizzas
    solution.mappingToCreatePizzaToppings('pizza_name','item description',solution.classStringToURI['topping'],solution.zdetor.hasTopping)
    # print(solution.g.serialize(format="turtle").decode("utf-8"))

    solution.saveGraph('./input_files/cw-data.ttl')