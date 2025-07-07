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
import re

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.base_agent import BaseAgent

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

LOGGER = logging.getLogger()

def main(args):

    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    os.environ['AZURE_OPENAI_MODEL'] = 'gpt-4o'

    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
        logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    else:
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=level)
    LOGGER.setLevel(level)

    ba = BaseAgent()
  
    ### Get input files content
    param_content = open(args.paramfile, 'r').read()
    pkg_content = open(args.pkgfile, 'r').read()

    ### PROMPT for llm
    prompt = f"""
You are an expert in SystemVerilog.  
You are given a SystemVerilog package file and a parameter file.   
<YongShan, please fill in the rest of your prompt here .....>

**Parameter File:**  
{param_content}  

**Package File:**
{pkg_content}


    """

    ba.kwargs['messages'] = [{'role': 'user', 'content': prompt}]
    res = ba.run()
    print(res.message.content)

    return True   



def remove_newline_and_markdown(json_str):
    """Remove newline characters and markdown formatting from a JSON string."""
    json_str = remove_newline(json_str)
    json_str = remove_markdown(json_str)
    return json_str

def remove_newline(json_str):
    """Remove newline characters from a JSON string."""
    import re
    # Remove newline characters
    json_str = re.sub(r'\n', '', json_str)
    # Remove extra spaces
    json_str = re.sub(r'\s+', ' ', json_str)
    return json_str

def remove_markdown(json_str):
    """Remove markdown formatting from a JSON string."""
    import re
    # Remove code block start and end
    json_str = re.sub(r"```json", '', json_str)
    json_str = re.sub(r"```", '', json_str)
    # Remove inline code
    json_str = re.sub(r"`", '', json_str)
    return json_str



if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='yongshan.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('--paramfile', default=None, required=True, help='param file')
    parser.add_argument('--pkgfile', default=None, required=True, help='pkg file')
    args = parser.parse_args()

    main(args)

