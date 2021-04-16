'''
Created on 01 April 2021
@author: zacharias.detorakis@city.ac.uk

Write SPARQL queries, according to the requirements in the following subtasks, and execute them over the created ontology and the generated data.

Subtask SPARQL.1 Perform reasoning with the created ontology and the generated data.2 Save the extended graph in turtle format (.ttl).
Subtask SPARQL.2 Return all the details of the restaurants that sell pizzas withouttomate (i.e., pizza bianca). Return the results as a CSV file.
Subtask SPARQL.3 Return the average prize of a Margherita pizza.
Subtask SPARQL.4 Return number of restaurants by city, sorted by state and numberof restaurants.
Subtask SPARQL.5 Return the list of restaurants with missing postcode.
'''



# Import Libraries
from rdflib import Graph
import pandas as pd
import owlrl

class Task4Solution(object):

    def __init__(self):

        #Initialise a graph
        self.g = Graph()

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

    def saveGraphOwl(self, file_output):
        """
        A function used to save a graph to a turle file
        ...

        Attributes
        ----------
        file_output : string
            the name of the file that the KG will be saved as (extension included)
        """

        self.g.serialize(destination=file_output, format='xml')
        print(f"{str(len(self.g))} triples saved in {file_output}.")

    def performReasoning(self, ontology_file):
        """
        A function used to expand a knowledge grpah with inferences using an ontology
        ...

        Attributes
        ----------
        ontology_file : string
            the name of the turtle file that has the reference ontology (extension included)
        """

        #We should load the ontology first
        self.loadGraph(ontology_file)
        # self.g.load(ontology_file,  format='ttl') #e.g., format=ttl
        print(f"Triples including ontology: {str(len(self.g))}.")

        #We apply reasoning and expand the graph with new triples 
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(self.g)
        print(f"Triples after OWL 2 RL reasoning: {str(len(self.g))}.")

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
    
    data_file = 'input_files/cw-data.ttl'
    ontology_file = 'input_files/zdetor.ttl'
    output_file = 'output_files/cw-data-reasoned.ttl'
    output_file_owl = 'output_files/cw-data-reasoned.owl'

    #################################
    #       Subtask SPARQL.1        #
    #################################
    #Initialise the class
    solution = Task4Solution()

    #Load the KG created from the csv with the asserted triples
    solution.loadGraph(data_file)
    print(f"Triples asserted in the KG: {str(len(solution.g))}.")

    #Perfom reasoning with the reference ontology (which is also parsed) and save the KG with the infered triples.
    solution.performReasoning(ontology_file)
    solution.saveGraphOwl(output_file_owl)
    solution.saveGraph(output_file)




    #####################################################################
    #                                                                   #
    #                   NEXT WE RUN THE SPARQL SCRIPTS                  #
    #                                                                   #
    #####################################################################
    print("\n\nResults for the SPARQL")
    print("----------------------")


    #################################
    #       Subtask SPARQL.2        #
    #################################
    # Return all the details of the restaurants that sell pizzas without tomate (i.e., pizza bianca). Return the results as a CSV file (20%).
    query_string_2 = """SELECT ?pizzaName ?description ?name ?addressLine
    WHERE{
            ?pizza a zdetor:Pizza;
                    zdetor:name ?pizzaName;
                    zdetor:isMenuItemOf ?restaurant;
                    zdetor:description ?description.
            ?restaurant zdetor:name ?name;
                        zdetor:hasAddress [ zdetor:addressLine ?addressLine] .
        FILTER (regex(LCASE(?pizzaName), \"white\") || regex(LCASE(?pizzaName), \"bianca\") || regex(LCASE(?pizzaName), \"bianco\") )
    #     FILTER NOT EXISTS {
    #        FILTER regex(?description, \"tomato\").
    #    }
    }

    """
    
    file_output = "./output_files/Results_2.csv"
    res_len_2, results_2 = solution.returnResults(query_string_2)
    results_2.to_csv(file_output)
    print(f"Restaurants that sell pizzas without tomate: {res_len_2}")
    print(f"{res_len_2} records saved in {file_output}")



    #################################
    #       Subtask SPARQL.3        #
    #################################
    # Return the average prize of a Margherita pizza (20%).
    query_string_3 = """ SELECT (sum(?price)/count(?pizza) as ?averagePrice) ?currency
    WHERE{
            ?pizza  a zdetor:MargheritaPizza;
                    zdetor:price ?price;
                    zdetor:currency ?currency;
                    zdetor:isMenuItemOf [ zdetor:hasAddress [ zdetor:addressLine ?addressLine] ] .
    }
    GROUP BY ?currency

    """

    res_len_3, results_3 = solution.returnResults(query_string_3)
    # results_3.to_csv("Results_3.csv")
    try:
        print(f"The average price for the Margherita Pizza is: {str(round(float(results_3.iloc[0].averagePrice),2))} {str(results_3.iloc[0].currency)}")
    except:
        print("No Margherita Pizza is found")



    #################################
    #       Subtask SPARQL.4        #
    #################################
    # Return number of restaurants by city, sorted by state and number of restaurants (20%).
    query_string_4 = """ SELECT ?cityName ?state (count(?restaurant) as ?num_of_restaurants)
    WHERE{
            ?restaurant a zdetor:Restaurant;
                        zdetor:hasAddress ?address .
            ?address    zdetor:hasCity ?city .
            ?city zdetor:name ?cityName .
            
            OPTIONAL {?address  zdetor:hasState [ zdetor:name ?state] .}
    }
    GROUP BY ?cityName
    ORDER BY ?state ?cityName

    """

    file_output = "./output_files/Results_4.csv"
    res_len_4, results_4 = solution.returnResults(query_string_4)
    results_4.to_csv(file_output)
    print(f"Unique cities with restaurants by state: {res_len_4}")
    print(f"{res_len_4} records saved in {file_output}")



    #################################
    #       Subtask SPARQL.5        #
    ################################# 
    # Return the list of restaurants with missing postcode (20%).
    query_string_5 = """ SELECT ?restaurant ?restaurantName ?postCode
    WHERE{
            ?restaurant a zdetor:Restaurant;
                        zdetor:hasAddress ?address ;
                        zdetor:name ?restaurantName .
            ?address    zdetor:hasCity ?city .
            OPTIONAL {?address  zdetor:postCode ?postCode .}
            
            FILTER( !bound( ?postCode ) )
    }

    """
    
    file_output = "./output_files/Results_5.csv"
    res_len_5, results_5 = solution.returnResults(query_string_5)
    results_5.to_csv(file_output)
    print(f"Number of restaurants with missing postcode: {res_len_5}")
    print(f"{res_len_5} records saved in {file_output}")