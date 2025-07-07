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

from lib.agents.cmd2json_agent import Cmd2jsonAgent
from lib.loading_animation import LoadingAnimation

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

stop_animation = False

def main(args):

    if args.userguide or (not args.cmd and not args.input_string):
        print_userguide()
        sys.exit(0)

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    ani = LoadingAnimation()
    ani.run()
    a = Cmd2jsonAgent()
    a.cmd = args.cmd
    a.expected_json_format = args.jsonformat
    a.input_string = args.input_string

    res = a.run()
    ani.stop()
    print()

    if args.debug:
        print('======================')
        print("cmd_output:")
        print('-----------------------')
        print(a.cmd_output)
        print('======================')
        print('======================')
        print('json:')
        print('-----------------------')
        data = res.message['content']
        print(json.dumps(json.loads(data), indent=4))
        print('======================')
    else:
        print(res.message['content'])

    return res.message['content']

def print_userguide():
    text = """

## Examples:

1. **Without --jsonformat**
    > cmd2json.py -c 'ls -al'
    > cmd2json.py -c 'ypcat passwd | grep lionelta'
    > cmd2json.py -c 'ypcat group | grep -P "^psgsiemens:"'
This will let the llm decide the json format.  

2. **With --jsonformat**
    > cmd2json.py -c 'ls -al' --jsonformat '{"files": [<filename>, <filename>, ...], "dirs": [<dirname>, <dirname>, ...]}'
This will force the llm to output the json in the specified format.  
    """
    gu.print_markdown(text, cursor_moveback=False)
    

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='cmd2json.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-j', '--jsonformat', default='', help='Expected JSON format')
    parser.add_argument('-ug', '--userguide', default=False, action='store_true', help='Show user guide')
    
    parser.add_argument('-c', '--cmd', default='', help='Command to run')
    parser.add_argument('-i', '--input_string', default='', help='Input string to be converted to JSON')

    args = parser.parse_args()

    main(args)

