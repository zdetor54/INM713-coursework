# Load back with memory-mapping = read-only, shared across processes.
from gensim.models import KeyedVectors


wv = KeyedVectors.load("Standalone_0.1/output_embedding/exp3/cw_data.embeddings", mmap='r')

# vector = wv.wv['pizza']  # Get numpy vector of a word
# print(vector)


similarity = wv.wv.similarity('pizza', 'https://www.city.ac.uk/ds/inm713/zacharias_detorakis#MargheritaPizza')
print('pizza - https://www.city.ac.uk/ds/inm713/zacharias_detorakis#MargheritaPizza: ', similarity)

similarity = wv.wv.similarity('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#PizzaTopping', 'https://www.city.ac.uk/ds/inm713/zacharias_detorakis#Pizza')
print('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#PizzaTopping - https://www.city.ac.uk/ds/inm713/zacharias_detorakis#Pizza: ', similarity)

similarity = wv.wv.similarity('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#State', 'https://www.city.ac.uk/ds/inm713/zacharias_detorakis#Pizza')
print('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#State - https://www.city.ac.uk/ds/inm713/zacharias_detorakis#Pizza: ', similarity)

similarity = wv.wv.similarity('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#addressLine', 'https://www.city.ac.uk/ds/inm713/zacharias_detorakis#Pizza')
print('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#addressLine - https://www.city.ac.uk/ds/inm713/zacharias_detorakis#Pizza: ', similarity)

similarity = wv.wv.similarity('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#PizzaTopping', 'https://www.city.ac.uk/ds/inm713/zacharias_detorakis#PepperoniTopping')
print('https://www.city.ac.uk/ds/inm713/zacharias_detorakis#PizzaTopping - https://www.city.ac.uk/ds/inm713/zacharias_detorakis#PepperoniTopping: ', similarity)

# result = wv.most_similar_cosmul(positive=['margherita'])

# most_similar_key, similarity = result[0]  # look at the first match

# print(f"{most_similar_key}: {similarity:.4f}")
# print(result)

#https://radimrehurek.com/gensim/models/keyedvectors.html
