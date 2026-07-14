"""Day 2 experiment: what is a token, really?

Answers three questions:
  1. Why can't LLMs count letters?
      the llm doesnt see letter what it sees is the tokens and it has only the token id(its vector
        form), it doesnt inherently knows how many letters it has so it basically guesses it.
  2. Why does non-English text cost more?
      the tokenizer are mostly trained on english vocabulary as most of the data is coming from
        english the algos like bpe compresses mostly english as it has highest frequency and the 
        other languages priority is reduced so they are not paired effectively hence use more tokens
  3. How stable is 'the same word' across contexts?
      i think the token id is different for the same words like if it is capitalized or after a 
      space or if its found i middle of some other word lets  say burning can be a single token 
      and burn can be a token where as burn, ing is also possible it entirely upto what algorithm
        we use. 

"""
import tiktoken

# GPT-4o's tokenizer — closest public analog to modern frontier models
enc = tiktoken.get_encoding("o200k_base")


def show(label: str, text: str) -> None:
    """Print a string, its token IDs, and its token pieces (decoded)."""
    ids = enc.encode(text)
    pieces = [enc.decode([i]) for i in ids]
    print(f"\n{label!r}")
    print(f"  text     : {text!r}")
    print(f"  token IDs: {ids}")
    print(f"  pieces   : {pieces}")
    print(f"  n_tokens : {len(ids)}   ({len(text)} chars, ratio={len(text)/len(ids):.2f})")


# Experiment 1: the strawberry problem
print("\n=== Experiment 1: Why can't LLMs count letters? ===")
show("strawberry", "strawberry")
show("strawberry (spaced)", "s t r a w b e r r y")
# TODO: predict what you'll see BEFORE running. How many tokens is 'strawberry'?
# How many for the spaced version? Which one could a model 'count' r's in?
# ans:: i know why the llms cant count letters but i am still not sure why it is able to 
# count it in spaced (if at all its able to do) because ultimately it always guesses it doesnt 
# really have a tool to count the letters let me know more about it



# Experiment 2: multilingual cost
print("\n=== Experiment 2: Non-English costs more ===")
show("English", "The weather is nice today.")
show("Hindi",   "आज मौसम अच्छा है।")
show("Telugu",  "ఈరోజు వాతావరణం బాగుంది.")
# TODO: for each, note the tokens-per-character ratio. What's the cost multiplier?
# ans:: 4.33 for english and hindi 3.40 which is surprisingly high i thought it would be lower
#  and for telugu it was 1.92

# Experiment 3: context sensitivity
print("\n=== Experiment 3: Same word, different tokens ===")
show("word alone",    "hello")
show("with space",    " hello")
show("capitalized",   "Hello")
show("mid-sentence",  "she said hello there")
# TODO: is 'hello' the same token every time? Why does this matter for
# prompt caching (which is exact-prefix match)?
#ans:: i am not sure if i understand this question

# Experiment 4: your own
# TODO: add ONE experiment of your own. Try something you're curious about:
# numbers ('1234567890'), code ('def hello_world():'), emoji, your own name,
# a URL, whatever. Predict then observe.
show("name", "uzair ahmed baig :)" )
show("emoji", "😊" )
show("url", "https://www.example.com/path/to/resource?query=param#fragment" )
show("a really long word", "pneumonoultramicroscopicsilicovolcanoconiosis" )


# Summary
print("\n=== Summary ===")
# TODO: after running everything, write 3-5 lines here as comments summarizing
# what you learned. This is not busywork — this is the artifact.

