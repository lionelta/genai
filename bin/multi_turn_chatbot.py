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
import threading
import itertools
import time
import tempfile

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
import lib.loading_animation

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.chatbot_agent import ChatbotAgent

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main(args):

    a = ChatbotAgent()
    a.faiss_dbs = args.loaddb
    a.kwargs['messages'] = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
    query = input("[ASSISTANT] Hi there, how can i help you today? (to end chat, press Ctrl-C)\n[USER] ")
    while True:
        a.kwargs['messages'].append({'role': 'user', 'content': query})
        res = a.run()
        fullres = ''
        print("[ASSISTANT] ", end='', flush=True)
        for chunk in res:
            print(chunk, end='', flush=True)
            fullres += chunk
        a.kwargs['messages'].append({'role': 'assistant', 'content': fullres})
        print('\n[USER] ', end='', flush=True)
        query = input()

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='chat.py', formatter_class=MyFormatter)
    parser.add_argument('-l', '--loaddb', default=None, nargs='+', help='Load the FAISS db')
    args = parser.parse_args()

    main(args)

