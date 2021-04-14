'''
Created on 01 April 2021
@author: zacharias.detorakis@city.ac.uk

'''

# Import Libraries
import sys
sys.path.append('./lib/')

import pandas as pd
import yake

# concatenate all the values from the categories column to create the string to perform the NLP on
def is_nan(x):
        return (x != x)

def createListOfFrequentTerms(df, column, max_ngram_size = 2, numOfKeywords = 40):
    concat_string = ''

    for val in df[column]:
        if is_nan(val) or val==None or val=="":
            pass
        else:
            concat_string = concat_string + ', ' + str(val)
    stop_words = []

    kw_extractor = yake.KeywordExtractor()

    # text = """spaCy is an open-source software library for advanced natural language processing, written in the programming languages Python and Cython. The library is published under the MIT license and its main developers are Matthew Honnibal and Ines Montani, the founders of the software company Explosion."""
    text = concat_string
    language = "en"
    deduplication_threshold = 0.9
    custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold, top=numOfKeywords, features=None)
    keywords = custom_kw_extractor.extract_keywords(text)

    sorted_list = []
    for kw in keywords:
        sorted_list.append(kw[0])
        print(kw)
    return sorted_list

input_csv = "./input_files/INM713_coursework_data_pizza_8358_1_reduced.csv"
input_csv = "./input_files/INM713_coursework_data_pizza_8358_1_reduced - small.csv"


df = pd.read_csv(filepath_or_buffer = input_csv, sep=',', quotechar='"',escapechar="\\")

frequent_restaurant_categories = createListOfFrequentTerms(df, 'item description', numOfKeywords = 10)

# frequent_pizza_classes = createListOfFrequentTerms(solution.df, 'menu item', numOfKeywords = 20)

# frequent_toppings = createListOfFrequentTerms(solution.df, 'item description', max_ngram_size=2, numOfKeywords = 40)