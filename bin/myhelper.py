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
import subprocess
import json

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.tool_agent import ToolAgent
from lib.loading_animation import LoadingAnimation

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

stop_animation = False

def main(args):

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    #ani = LoadingAnimation()
    #ani.run()

    a = ToolAgent()
    a.toolfile = os.path.join(rootdir, 'toolfiles', 'myhelper_toolfile.py')
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]

    ### Print out all the toolfile loaded agents
    if args.debug:
        print("These are all the available tools:")
        tf = a.load_toolfile()
        tf.print_all_tools()

    res = a.run()
    #ani.stop()

    if args.debug:
        print("=================================================")
        print("Question: ", args.query)
        print("=================================================")
        print(f'response from LLM: {res}')
        print("=================================================")

    reslist = a.execute_response(res)
    if args.debug:
        print(f"Response from execute: {reslist}")
        print("=================================================")

    for e in reslist:
        if e and 'missing_params' in e:
            print(e)

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='myhelper.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-q', '--query', default=None, help='Query string')
    args = parser.parse_args()

    main(args)

