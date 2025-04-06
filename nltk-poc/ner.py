
import nltk
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk import ne_chunk

nltk.download('maxent_ne_chunker_tab')
nltk.download('words')

text = "Apple Inc. is planning to open a new store in New York next to Central Park."
tokens = word_tokenize(text)
pos_tags = pos_tag(tokens)

named_entities = ne_chunk(pos_tags)
print(named_entities)
# This prints a tree structure with recognized entities