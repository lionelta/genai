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


    ### PROMPT for llm
    prompt = f"""
You are an expert in SystemVerilog.  
Let's think step by step to solve the problem.  

**Instruction:**
1. You will be given a parameter yaml data as input.  
2. You need to generate a attribute yaml data based on the parameter yaml information.  
3. Do not provide any explanation or comments in the output.
4. The output should be in the format of a YAML string, without any markdown formatting.

Here's is an example:  

**Example Parameter YAML:**
rtl_module_name: axi4lite_bypass_word_fp_sf
parameters:
  parameter_1:
    name: powerdown_mode
    default_value: POWERDOWN_MODE_TRUE
    data_type: powerdown_mode_false_true_type
    data_pkg: psg_std_pkg
    data_members:
      - POWERDOWN_MODE_TRUE
      - POWERDOWN_MODE_FALSE
  parameter_2:
    name: if_word_enable_attr
    default_value: IF_BYTE
    data_type: if_word_enable_attr_type
    data_pkg: if_word_enable_attr_type_pkg
    data_members:
      - IF_BYTE
      - IF_WORD
  parameter_3:
    name: if_port_0_mode_attr
    default_value: PORT0_BYPASS_A
    data_type: if_port_0_mode_attr_type
    data_pkg: if_port_0_mode_attr_type_pkg
    data_members:
      - PORT0_BYPASS_A
      - PORT0_BYPASS_B
      - PORT0_REG_A
      - PORT0_REG_B
  parameter_4:
    name: if_port_1_mode_attr
    default_value: PORT1_BYPASS_A
    data_type: if_port_1_mode_attr_type
    data_pkg: if_port_1_mode_attr_type_pkg
    data_members:
      - PORT1_BYPASS_A
      - PORT1_BYPASS_B
      - PORT1_REG_A
      - PORT1_REG_B
  parameter_5:
    name: voltage_level_attr
    default_value: VTINY
    data_type: voltage_level_attr_type
    data_pkg: voltage_level_attr_type_pkg
    data_members:
      - VTINY
      - VLOW
      - VMED
      - VHIGH
  parameter_6:
    name: output_0_invert_attr
    default_value: NONINVERT
    data_type: output_invert_attr_type
    data_pkg: output_invert_attr_type_pkg
    data_members:
      - NONINVERT
      - INVERT
  parameter_7:
    name: output_1_invert_attr
    default_value: NONINVERT
    data_type: output_invert_attr_type
    data_pkg: output_invert_attr_type_pkg
    data_members:
      - NONINVERT
      - INVERT

** Example Attribute YAML: **
bcm_attributes:
  powerdown_mode:
    attr_desc: powerdown_mode
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: POWERDOWN_MODE_TRUE
    sv_type: psg_std_pkg::powerdown_mode_false_true_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [POWERDOWN_MODE_TRUE, POWERDOWN_MODE_FALSE]
  if_word_enable_attr:
    attr_desc: if_word_enable_attr
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: IF_BYTE
    sv_type: if_word_enable_attr_type_pkg::if_word_enable_attr_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [IF_BYTE, IF_WORD]
  if_port_0_mode_attr:
    attr_desc: if_port_0_mode_attr
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: PORT0_BYPASS_A
    sv_type: if_port_0_mode_attr_type_pkg::if_port_0_mode_attr_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [PORT0_BYPASS_A, PORT0_BYPASS_B, PORT0_REG_A, PORT0_REG_B]
  if_port_1_mode_attr:
    attr_desc: if_port_1_mode_attr
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: PORT1_BYPASS_A
    sv_type: if_port_1_mode_attr_type_pkg::if_port_1_mode_attr_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [PORT1_BYPASS_A, PORT1_BYPASS_B, PORT1_REG_A, PORT1_REG_B]
  voltage_level_attr:
    attr_desc: voltage_level_attr
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: VTINY
    sv_type: voltage_level_attr_type_pkg::voltage_level_attr_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [VTINY, VLOW, VMED, VHIGH]
  output_0_invert_attr:
    attr_desc: output_0_invert_attr
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: NONINVERT
    sv_type: output_invert_attr_type_pkg::output_invert_attr_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [NONINVERT, INVERT]
  output_1_invert_attr:
    attr_desc: output_1_invert_attr
    configuration_type: CUSTOM
    function_type: VIRTUAL
    default: NONINVERT
    sv_type: output_invert_attr_type_pkg::output_invert_attr_type
    attr_use_type: none
    attr_constrains_pwr_model: false
    affects_timing: false
    affects_power: false
    settings: [NONINVERT, INVERT]


Here's the parameter yaml data you need to use:  
**Parameter YAML:**
{param_content}

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

    parser = argparse.ArgumentParser(prog='yongshan2.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('--paramfile', default=None, required=True, help='param file')
    parser.add_argument('--outfile', default=None, required=True, help='output file')
    args = parser.parse_args()

    main(args)

