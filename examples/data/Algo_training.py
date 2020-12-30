
#WIP. Refer training_script.sh for working code
from transformers import Trainer



from transformers import GPT2Tokenizer, GPT2LMHeadModel
from nltk.tokenize import sent_tokenize
from numpy.random import choice
import torch


tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')

trainer=Trainer(model=model,tokenizer=tokenizer, train_dataset='wikitext-2/wiki.train.tokens', eval_dataset='wikitext-2/wiki.val.tokens')