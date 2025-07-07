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

from lib.agents.explain_code_agent import ExplainCodeAgent
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

    ani = LoadingAnimation()

    a = ExplainCodeAgent()
    a.kwargs['stream'] = True

    for f in args.files:
        print('==================================================')
        print(f"File: {f}")
        print('--------------------------------------------------')
        if not os.path.isfile(f):
            ani.stop()
            print(f"File {f} does not exist.")
        else:
            a.codefile = f
            a.explanation = args.explanation
            ani.run()
            res = a.run()
            ani.stop()
            fullres = ''
            for chunk in res:
                print(chunk, end='', flush=True)
                fullres += chunk
            time.sleep(1) # to allow the last print to flush
            print()
            print('==================================================')
            print(f"File: {f}")
            print("(Markdown format)")
            print('--------------------------------------------------')
            gu.print_markdown(fullres, cursor_moveback=False)


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='explain_code.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-f', '--files', default=None, required=True, nargs='+', help='Files')
    parser.add_argument('-e', '--explanation', default='high', choices=['high', 'mid', 'low'], help='Level of explanation you are expecting. (high=less detailed, mid=moderate, low=very detailed)')

    args = parser.parse_args()

    main(args)

