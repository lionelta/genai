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

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.python_coding_agent import PythonCodingAgent
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

    if args.userguide:
        print_userguide()
        sys.exit(0)

    ani = LoadingAnimation()
    ani.run()

    a = PythonCodingAgent()
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    res = a.run()
    ani.stop()

    print("=================================================")
    print("Question: ", args.query)
    print("=================================================")
    print("Code: ")
    a.print_code()
    print("=================================================")

    raw_input = input("Do you want to run the code? (y/n): ")
    if raw_input.lower() != 'y':
        print("Exiting without running the code.")
    else:
        print("Running the code...")
        output = a.execute_code(systemcall=True)
        #print(f"{output}")
    print("The code is saved in: ", a.codefile)
    return a.codefile

def print_userguide():
    print("""
    > automater.py -q 'show me all the python files from current folder, one per line.'
    > automater.py -q 'print out all the lines which matches the word "myhelper.py" in file ./unittests/manual_test_myhelper'
    > automater.py -q 'replace all the word "myhelper" to "yourfriend" in file ./unittests/manual_test_myhelp, and save it to /tmp/a.b.c'
    > automater.py -q 'rename all the files in current folder from <filename> to lionel_<filename>.txt'
    """)

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='automater.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-q', '--query', default=None, help='Query string')
    parser.add_argument('-ug', '--userguide', default=False, action='store_true', help='Print user guide')

    args = parser.parse_args()

    main(args)

