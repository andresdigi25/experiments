from nltk.classify import NaiveBayesClassifier
from nltk.classify.util import accuracy

# Example training data
train_data = [
    ({'word': 'excellent'}, 'positive'),
    ({'word': 'great'}, 'positive'),
    ({'word': 'terrible'}, 'negative'),
    ({'word': 'bad'}, 'negative')
]

# Train classifier
classifier = NaiveBayesClassifier.train(train_data)

# Test
test_data = [
    ({'word': 'awesome'}, 'positive'),
    ({'word': 'poor'}, 'negative')
]

print("Accuracy:", accuracy(classifier, test_data))
print(classifier.classify({'word': 'awesome'}))  # Should predict 'positive'
print(classifier.classify({'word': 'bad'})) 