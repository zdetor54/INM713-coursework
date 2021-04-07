# Import Libraries
from rdflib import Graph
import pandas as pd
import owlrl

#Functions needed for the saving and the reasoning of the graph

def saveGraph(graph, file_output):
    """
    A function used to save a graph to a turle file
    ...

    Attributes
    ----------
    graph : Graph
        the KG to be saved
    file_output : string
        the name of the file that the KG will be saved as (extension included)
    """

    graph.serialize(destination=file_output, format='ttl')
    print("Triples including ontology: '" + str(len(graph)) + "' saved.")

def performReasoning(graph, ontology_file):
    """
    A function used to expand a knowledge grpah with inferences using an ontology
    ...

    Attributes
    ----------
    graph : Graph
        the KG to be expanded
    file_output : string
        the name of the turtle file that has the reference ontology (extension included)
    """

    print("Triples including ontology: '" + str(len(graph)) + "'.")
    
    #We should load the ontology first
    graph.load(ontology_file,  format='ttl') #e.g., format=ttl


    #We apply reasoning and expand the graph with new triples 
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(graph)

    print("Triples after OWL 2 RL reasoning: '" + str(len(graph)) + "'.")

def returnResults(g, query_string):
    """
    A function used to run the sparql query from the query_string on the KG g and return the results as a dataframe as well as the length of the results
    ...

    Attributes
    ----------
    g : Graph
        the KG to be queries
    query_string : string
        the string containing the SPARQL query
    """

    #Excecute the query
    qres = g.query(query_string)


    #parse the results and append them to a list of objects that will be converted to a dataframe
    results = []
    for row in qres:
        element = {}
        for key in row.labels.keys():
            element[key]= row[row.labels[key]]
        results.append(element)
    
    return len(qres), pd.DataFrame(results)

#Initialise a graph
g = Graph()

# Load the asserted tripples from the KG
g.parse("cw-data.ttl", format="ttl")
print("Loaded '" + str(len(g)) + "' triples.")

#perform the reasoning  with the created ontology and save to a new KG in ttl format
performReasoning(g,'zdetor.ttl')
saveGraph(g, 'cw-data-reasoned.ttl')

## Subtask SPARQL.2 
# Return all the details of the restaurants that sell pizzas without tomate (i.e., pizza bianca). Return the results as a CSV file (20%).

print("\n\nResults for the SPARQL")
print("---------------------- \n")

query_string_2 = """SELECT ?pizzaName ?description ?name ?addressLine
WHERE{
        ?pizza a zdetor:Pizza;
                zdetor:name ?pizzaName;
                zdetor:isMenuItemOf ?restaurant;
                zdetor:description ?description.
        ?restaurant zdetor:name ?name;
                    zdetor:hasAddress [ zdetor:addressLine ?addressLine] .
    FILTER (regex(LCASE(?pizzaName), \"white\") || regex(LCASE(?pizzaName), \"bianca\") || regex(LCASE(?pizzaName), \"bianco\") ).
#    FILTER NOT EXISTS {
#        FILTER regex(?description, \"tomato\").
#    }
}

"""
res_len_2, results_2 = returnResults(g, query_string_2)
results_2.to_csv("Results_2.csv")
print(f"Restaurants that sell pizzas without tomate: {res_len_2}")



## Subtask SPARQL.3 
# Return the average prize of a Margherita pizza (20%).
query_string_3 = """ SELECT (sum(?price)/count(?pizza) as ?averagePrice)
WHERE{
        ?pizza  a zdetor:MargheritaPizza;
                zdetor:price ?price;
                zdetor:isMenuItemOf [ zdetor:hasAddress [ zdetor:addressLine ?addressLine] ] .
}
#GROUP BY ?pizza ?addressLine

"""

res_len_3, results_3 = returnResults(g, query_string_3)
results_3.to_csv("Results_3.csv")
print(f"The average price for the Margherita Pizza is: ${str(round(float(results_3.iloc[0].averagePrice),2))}")

## Subtask SPARQL.4 
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

res_len_4, results_4 = returnResults(g, query_string_4)
results_4.to_csv("Results_4.csv")
print(f"Unique cities with restaurants by state: {res_len_4}")


## Subtask SPARQL.5 
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
res_len_5, results_5 = returnResults(g, query_string_5)
results_5.to_csv("Results_5.csv")
print(f"Number of restaurants with missing postcode: {res_len_5}")