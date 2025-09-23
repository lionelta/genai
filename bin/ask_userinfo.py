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

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

from lib.agents.tool_agent import ToolAgent
from lib.agents.chatbot_agent import ChatbotAgent

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'


def main(args):

    if args.examples:
        print_examples()
        return True

    os.environ['AZURE_OPENAI_API_KEY'] = os.getenv("AZURE_OPENAI_API_KEY", 'show me the money')
    os.environ['AZURE_OPENAI_MODEL'] = os.getenv("AZURE_OPENAI_MODEL", 'gpt-4.1')

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    a = ToolAgent()
    a.toolfile = os.path.join(rootdir, 'toolfiles', 'userinfo_toolfile.py')
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
  
    ### Dispatch query to chatbot agent if no matching tool calls are found
    called_tool = a.get_called_tools(res)
    if args.debug:
        print(f"called_tool: {pformat(called_tool)}")
    if not called_tool or not a.is_function_name_in_loaded_tools(called_tool['function']):
        dispatch_to_chatbot_agent(args.query)
        sys.exit()
    
    if called_tool['missing_params']:
        a.kwargs['messages'].append({'role': 'assistant', 'content': 'missing_params:' + str(called_tool['missing_params'])})
        for key in called_tool['missing_params']:
            value = input(f"please provide the missing parameters({key}): ")
            a.kwargs['messages'].append({'role': 'user', 'content': f" parameter({key}): {value} "})

    #pprint(a.kwargs['messages'])
    res = a.run()
    if args.debug:
        print(f"Response from tool: {res}")

    reslist = a.call_tool(res)
    if args.debug:
        print(f"Response from execute tool: {reslist}")
        print("=================================================")
    
    print(reslist)


def dispatch_to_chatbot_agent(query):
    """Dispatch the query to a chatbot agent if no tool calls are found."""
    print("No tool calls found in the response. Dispatching to common Q&A llm agent")
    ca = ChatbotAgent()
    ca.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    ca.kwargs['stream'] = False
    res = ca.run()
    print(res.message.content)
    return res.message.content

def examples():
    examples = """
- linux groups of user wplim
- what is the email of user chin yin 
- what is chin yin userid
- what is chin yin wwid
- show me details of wwid:12128309
- Let us think step by step. Provide the reporting structure of Lionel all the way up to Arvind.
"""
    return examples

def print_examples():
    print(examples())


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='adm_userinfo.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-q', '--query', default=None, help='Query string')
    parser.add_argument('--examples', default=False, action='store_true', help='Show example queries')
    args = parser.parse_args()

    main(args)

