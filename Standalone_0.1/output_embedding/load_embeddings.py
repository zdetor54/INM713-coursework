# Load back with memory-mapping = read-only, shared across processes.
from gensim.models import KeyedVectors


wv = KeyedVectors.load("pizza.embeddings", mmap='r')

vector = wv['pizza']  # Get numpy vector of a word
print(vector)

for key in wv.wv.vocab:
    print(key)

similarity = wv.similarity('pizza', 'giuseppe')

print(similarity)


similarity = wv.similarity('ham', 'mushroom')

print(similarity)



similarity = wv.similarity('tomato', 'pizza')
print(similarity)


similarity = wv.similarity('http://www.co-ode.org/ontologies/pizza/pizza.owl#TomatoTopping', 'http://www.co-ode.org/ontologies/pizza/pizza.owl#Pizza')
print(similarity)

similarity = wv.similarity('http://www.co-ode.org/ontologies/pizza/pizza.owl#TomatoTopping', 'http://www.co-ode.org/ontologies/pizza/pizza.owl#Margherita')
print(similarity)


similarity = wv.similarity('pizza', 'http://www.co-ode.org/ontologies/pizza/pizza.owl#Pizza')
print(similarity)


result = wv.most_similar_cosmul(positive=['margherita'])

most_similar_key, similarity = result[0]  # look at the first match

print(f"{most_similar_key}: {similarity:.4f}")
print(result)

#https://radimrehurek.com/gensim/models/keyedvectors.html
