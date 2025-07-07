#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
Confirm Working with :-
- venv: 3.10.11_sles12_cuda
- host: asccf06294100.sc.altera.com

'''
import os
import sys
import logging
import warnings
import argparse
import importlib.util
from pprint import pprint, pformat
#from FlagEmbedding import BGEM3FlagModel

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main():

    LOGGER = logging.getLogger(__name__)
    level = logging.INFO
    if '--debug' in ' '.join(sys.argv):
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

    emb_model = gu.load_default_settings()['emb_model']
    model = gu.load_embedding_model(emb_model)


    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(emb_model)
    model.max_seq_length = 512

    questions = ['how much protein should a female eat',
        'what is your name',
        'how to set a flow to non-gating'

    ]
    answers = ['As a general guideline, the recommended dietary allowance (RDA) for protein is 46 grams per day for women',
        'my name is lionel tan',
        'to set a flow to non-gating, you need to edit the tool.cth file, and add the following line: <flow gating="false">'
    ]
    for i,q in enumerate(questions):
        a = answers[i]
        q_emb = model.encode([q])
        a_emb = model.encode([a])
        scores = (q_emb @ a_emb.T) * 100
        print(f'Question: {q}')
        print(f'Answer: {a}')
        print(f'Score: {scores[0][0]:.2f}')
        #print(scores.tolist())
        print('======================================')

if __name__ == '__main__':
    main()

