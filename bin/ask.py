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
    if args.debug:
        pprint(args)

    LOGGER = logging.getLogger()
    level = logging.INFO
    if args.clean:
        level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    a = ChatbotAgent()
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    if args.query == '-':
        a.kwargs['messages'] = [{'role': 'user', 'content': sys.stdin.read()}]
    a.faiss_dbs = args.loaddb

    if args.scripting_mode:
        a.kwargs['stream'] = False
        res = a.run()
        print(res.message.content)
        return


    ani = lib.loading_animation.LoadingAnimation()
    ani.run()
    res = a.run()
    ani.stop()
    time.sleep(1)
    fullres = ''
    for chunk in res:
        print(chunk, end='', flush=True)
        fullres += chunk

    time.sleep(1)   # wait for the last chunk to finish
    print()
    print('==================================================')
    print("(Markdown format)")
    print('--------------------------------------------------')
    gu.print_markdown(fullres, cursor_moveback=False)


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='ask.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('--clean', action='store_true', default=True, help='Clean mode')
    
    parser.add_argument('-l', '--loaddb', default=None, nargs='+', help='Load the FAISS db')
    parser.add_argument('-q', '--query', default=None, help='Query string. If "-" is provided, will read from stdin.')

    parser.add_argument('-sm', '--scripting_mode', action='store_true', default=False, help='Will print response in non-streaming mode. Useful for scripting.')
    args = parser.parse_args()

    main(args)

