import nltk
from nltk.corpus import gutenberg

# List available texts
print(gutenberg.fileids())

# Read a specific text
hamlet = gutenberg.words('shakespeare-hamlet.txt')
print(len(hamlet))

# Calculate statistics
hamlet_text = nltk.Text(hamlet)
hamlet_text.vocab()  # Vocabulary