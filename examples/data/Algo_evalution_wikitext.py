
#CODE to evaulate loss on 10 random samples from the WikiText-2 test set

from transformers import GPT2Tokenizer, GPT2LMHeadModel
from nltk.tokenize import sent_tokenize
from numpy.random import choice
import torch



tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')
#text = "Replace me by any text you'd like."

with open('wikitext-2/wiki.test.tokens') as f:
    text = f.read()

tokenized_text = sent_tokenize(text)
rand10=choice(tokenized_text, 10)

def score(sentence):
    encoded_input = tokenizer(text, return_tensors='pt')
    output = model(**encoded_input, labels=encoded_input['input_ids'])
    loss = float(output.loss)
    return loss

loss_sum=0
for sent in rand10:
    loss=score(sent)
    loss_sum+=loss

mean_loss = loss_sum/10

def main():
    return mean_loss
