from nltk import CFG
from nltk.parse.chart import ChartParser

# Define a simple grammar
grammar = CFG.fromstring("""
S -> NP VP
NP -> Det N | Det N PP
VP -> V NP | V NP PP
PP -> P NP
Det -> 'the' | 'a'
N -> 'dog' | 'cat' | 'ball'
V -> 'chased' | 'saw'
P -> 'with' | 'by'
""")

parser = ChartParser(grammar)
sentence = "the dog chased the cat".split()
for tree in parser.parse(sentence):
    print(tree)
    with open("parse_tree.txt", "w") as f:
        f.write(tree.pformat())