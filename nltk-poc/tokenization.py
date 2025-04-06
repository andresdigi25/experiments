import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

text = "Hello world. This is a test sentence. How are you doing today?"
sentences = sent_tokenize(text)
print(sentences)

words = word_tokenize(text)
print(words)

