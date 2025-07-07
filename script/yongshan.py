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
Let's think step by step to solve the problem.  

You are given a SystemVerilog package file and a parameter file.   

**INSTRUCTION**
1. Cross-reference the listed down the extracted parameter to map with the correct Enum list based on the package name and package type. 
2. Report out the mapped information in yaml format, whereby:
   a. The top level key is "bcm_attributes".
   b. follow by the parameter name as each key of dictionary.
   c. under each parameter name key, 
      - attr_desc which is similar to the parameter name, 
      - configuration_type which is set to "CUSTOM", 
      - function_type which is set to "VIRTUAL", 
      - default is the default value of the parameter, 
      - sv_type which is combination of "package_name::package_type", 
      - attr_use_type is set to "none", 
      - attr_constrains_pwr_model is set to "false", 
      - affects_timing is set to "false", 
      - affects_power is set to "false"
      - settings is the list of enum value.

Do not include any other text or explanation in the response.    
Only provide the generated final response in yaml string (without any markdown or backtick)!    


**Parameter File:**  
{param_content}  
  
  
**Package File:**
{pkg_content}
"""

    prompt += """
`idndef PSG_STD_PKG
`define PSG_STD_PKG
package psg_std_pkg;
typedef enum bit[0:0] {FALSE=0, TRUE=1} true_false_type;
typedef enum bit[0:0] {DISABLE=0, ENABLE=1} enable_disable_type;
typedef enum bit[0:0] {OFF=0, ON=1} on_off_type;
typedef enum bit[0:0] {POWERDOWN_MODE_TRUE=0, POWERDOWN_MODE_FALSE=1} powerdown_mode_false_true_type;
endpackage // psg_std_pkg
`endif // PSG_STD_PKG
    """

    ba.kwargs['messages'] = [{'role': 'user', 'content': prompt}]
    res = ba.run()
    print(res.message.content)

    ### Write the response to a file
    with open(args.outfile, 'w') as outfile:
        # Remove newline characters and markdown formatting
        cleaned_response = remove_markdown(res.message.content)
        outfile.write(cleaned_response)
    print("Output written to:", args.outfile)




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
    json_str = re.sub(r"```yaml", '', json_str)
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
    parser.add_argument('--outfile', default=None, required=True, help='output file')
    args = parser.parse_args()

    main(args)

