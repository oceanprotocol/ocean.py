

from transformers import pipeline, set_seed
import sys
generator = pipeline('text-generation', model='./new_models')
set_seed(42)

def complete_text(text):
    r = generator(text, max_length=30, num_return_sequences=5)
    return r

def main():
    result = complete_text(sys.argv[1])
    print(result)
    return(result)
