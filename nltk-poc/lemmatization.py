import nltk
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()
words = ["running", "runs", "ran", "better", "swimming", "swam"]
lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
print(lemmatized_words)

print(lemmatizer.lemmatize("running", pos="v"))
print(lemmatizer.lemmatize("better", pos="a"))