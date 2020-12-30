from transformers import pipeline, set_seed
import sys
generator = pipeline('text-generation', model='./new_models')
set_seed(42)

def score_text(text):
    encoded_input = tokenizer(text, return_tensors='pt')
    output = model(**encoded_input, labels=encoded_input['input_ids'])
    loss = float(output.loss)
    return loss
    

def main():
    result = score_text(sys.argv[1])
    print(result)
    return(result)