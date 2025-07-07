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

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.chatbot_agent import ChatbotAgent
from lib.agents.sql_coding_agent import SqlCodingAgent
from lib.agents.python_coding_agent import PythonCodingAgent
from lib.agents.base_agent import BaseAgent
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
    ani.run()

    a = BaseAgent()
    a = SqlCodingAgent()
    a.cnffile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sql_cnf_files', 'aiddac.cnf'))
    a.tables = ["build_cell_quality_breakdowns", "build_cell_quality_metric_statuses", "build_cell_quality_metrics", "build_drop_reviews", "build_drops", "build_flow_quality_metrics", "build_tags", "cell_types", "cell_unneeded_checkers", "cells", "checkers", "di_checks", "domains", "flow_checkers", "flows", "folder_names", "master_repo_groups", "master_repo_unneeded_checkers", "master_repos", "milestones", "nightly_builds", "nightly_builds_backup", "repo_bom_compliancies", "repo_boms", "repo_groups", "roles", "subsystem_ips", "thread_milestones", "threads", "user_repo_groups", "user_role_repos", "user_roles", "users"]
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    table_schemas = a.get_create_table_statements()
    sqlcnf = open(a.cnffile).read()
    fullres = ''
    print('----------------------------------------')


    b = PythonCodingAgent()
    b.kwargs['model'] = 'llama3.3'
    b.kwargs['stream'] = False 
    b.kwargs['options']['num_ctx'] = 11111
    b.kwargs['options']['temperature'] = 0.0
    b.kwargs['options']['top_p'] = 0.0
    b.systemprompt = f'''You are a programming expert in mysql and python.  
    You will be given a/some sql create table statement(s).   
    You will be given the sql config file.  
    Help generate Python code based on user requests.   You can incorperate sql commands in the python code.   
    Do not provide any explanation or any other information. 
    Do not provide the Python code in markdown format or wrap it with triple backticks.  
    Just provide the python code plain and raw.    

    **Create Table Statement:** 
    {table_schemas}   

    **SQL Config File:**
    {sqlcnf}
    '''
    b.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    LOGGER.debug(b.kwargs['messages'])
    res = b.run()
    ani.stop()
    
    print("=================================================")
    print("Question: ", args.query)
    print("=================================================")

    if not args.yes:
        print("Code: ")
        b.print_code()
        print("=================================================")
        raw_input = input("Do you want to run the code? (y/n): ")
    else:
        raw_input = 'y'
    if raw_input.lower() != 'y':
        print("Exiting without running the code.")
    else:
        print("Running the code...")
        output = b.execute_code()
        print(f"{output}")
    print("The code is saved in: ", b.codefile)
    return b.codefile

    
        
    

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='ask.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-q', '--query', default=None, help='Query string')
    parser.add_argument('-y', '--yes', default=False, action='store_true', help='Answer "y" to all questions')

    args = parser.parse_args()

    main(args)

