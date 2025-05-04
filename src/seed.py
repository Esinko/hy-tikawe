import random
from collections import defaultdict
from database.params import database_params
from database.abstract import AbstractDatabase
from database.connection import DatabaseConnection

# Training data
titles = [
    "Evalception", "Tiny Ternary", "Regex Only", "DOMless DOM", "Emoji Code",
    "Falsy Fun", "typeof Wizardry", "SetTimeout Art", "Console Golf", "Proxy Everything",
    "NaN Shenanigans", "Template Literal Abuse", "this is Confusing", "Garbage Collector Puzzle",
    "Constructor Chaos", "Everything Is a String", "Operator Overdose", "Event Loop Wizardry",
    "Script Inside Script", "Function.toString Magic"
]

descriptions = [
    "Create a function that uses eval to run itself.",
    "Implement FizzBuzz using only ternary operators.",
    "Solve a problem using only regular expressions.",
    "Manipulate the DOM without using document or window.",
    "Use only emojis to output numbers 1–10.",
    "Only use falsy values to build logic.",
    "Build logic using only the typeof operator.",
    "Create an animation using setTimeout and console.log.",
    "Print a pattern in as few characters as possible.",
    "Use Proxy to trap object behavior.",
    "Encode and decode data using NaN.",
    "Use template literals to build a working app.",
    "this should behave differently in the same function.",
    "Write code that breaks due to garbage collection.",
    "Create logic using only constructors and new.",
    "Store everything as strings and still build an app.",
    "Use only !, ~, and + to create logic.",
    "Force confusing execution order using async tricks.",
    "Inject and run another script tag from code.",
    "Hide logic inside .toString() overrides."
]

# Utils to create markov chain
def build_markov_chain(sentences):
    chain = defaultdict(list)
    for sentence in sentences:
        words = ["<S>"] + sentence.split() + ["<E>"]
        for i in range(len(words) - 2):
            key = (words[i], words[i + 1])
            chain[key].append(words[i + 2])
    return chain

def generate_sentence(chain, max_words=20):
    current = ("<S>", random.choice([k[1] for k in chain if k[0] == "<S>"]))
    result = [current[1]]
    for _ in range(max_words - 1):
        next_word = random.choice(chain.get(current, ["<E>"]))
        if next_word == "<E>":
            break
        result.append(next_word)
        current = (current[1], next_word)
    return " ".join(result)

# Build chains with training data
title_chain = build_markov_chain(titles)
desc_chain = build_markov_chain(descriptions)

# Create dummy challenges
n = 50000

db = db = AbstractDatabase(connection=DatabaseConnection("../main.db", "../db/schema.sql", "../db/init.sql").open())
for _ in range(n + 1):
    db.create_challenge(generate_sentence(title_chain), generate_sentence(desc_chain), random.randint(1, 3), 0, False)

db.connection.close()
