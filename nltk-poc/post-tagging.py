import nltk
from nltk.tokenize import word_tokenize
from nltk import pos_tag

# Ensure the required resource is downloaded
nltk.download('averaged_perceptron_tagger_eng')

text = "Python is a great programming language"
tokens = word_tokenize(text)
tagged = pos_tag(tokens)
print(tagged)