from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist

text = "This is a sample text. This text contains repeated words to demonstrate frequency distribution."
tokens = word_tokenize(text)

# Create frequency distribution
fdist = FreqDist(tokens)

# Most common words
print(fdist.most_common(5))
# Output: [('This', 2), ('text', 2), ('is', 1), ('a', 1), ('sample', 1)]

# Plot frequency distribution
fdist.plot(30, cumulative=False)  # Requires matplotlib