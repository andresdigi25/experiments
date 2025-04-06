from nltk.stem import PorterStemmer

stemmer = PorterStemmer()
words = ["running", "runs", "ran", "runner", "easily", "fairly"]

stemmed_words = [stemmer.stem(word) for word in words]
print(stemmed_words)