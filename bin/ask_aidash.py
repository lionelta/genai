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

from lib.agents.chatbot_agent import ChatbotAgent
from lib.agents.sql_coding_agent import SqlCodingAgent
from lib.agents.python_coding_agent import PythonCodingAgent
from lib.agents.base_agent import BaseAgent
from lib.loading_animation import LoadingAnimation
import lib.genai_utils as gu

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

stop_animation = False

def main(args):

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.userguide:
        print_user_guide()
        return

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    ani = LoadingAnimation()
    ani.run('')

    a = BaseAgent()
    a = SqlCodingAgent()
    a.cnffile = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'sql_cnf_files', 'aiddac.cnf'))
    a.tables = ["build_cell_quality_breakdowns", "build_cell_quality_metric_statuses", "build_cell_quality_metrics", "build_drop_reviews", "build_drops", "build_flow_quality_metrics", "build_tags", "cell_types", "cell_unneeded_checkers", "cells", "checkers", "di_checks", "domains", "flow_checkers", "flows", "folder_names", "master_repo_groups", "master_repo_unneeded_checkers", "master_repos", "milestones", "nightly_builds", "nightly_builds_backup", "repo_bom_compliancies", "repo_boms", "repo_groups", "roles", "subsystem_ips", "thread_milestones", "threads", "user_repo_groups", "user_role_repos", "user_roles", "users"]
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    table_schemas = a.get_create_table_statements()
    sqlcnf = open(a.cnffile).read()


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

    
       
def print_user_guide():
    text = """

## Here are a few useful prompting examples to get you started:

1. **Aidash User Guide**

    1. `Report Result For A Build-tag`
    report status for all attributes from build_cell_quality_metrics, for thread_milestones.milestone=RTL0.5, build_tag_id=bypass_reg-a0-0.5rc-25ww15g in a tabulated format. If the column is an id, convert it to their respective name.

    2. `Compare Two Builds`
    report status for all attributes from build_cell_quality_metrics, for thread_milestones.milestone=RTL0.5, build_tag_id=bypass_reg-a0-0.5rc-25ww15g in a tabulated format. If the column is an id, convert it to their respective name. Do the same for thread_milestones.milestone=RTL0.5, build_tag_id=bypass_reg-a0-0.5rc-25ww15h. After that, compare the result from the 2 tables and summarize the differences  in a tabulated format, with columns of (flow name, checker name, cell name, result from tag bypass_reg-a0-0.5rc-25ww15g, result from tag bypass_reg-a0-0.5rc-25ww15h)

2. **Dropbox User Guide**

    1. `Report All available repo_groups`
    list all repo_groups

    2. `Report all repos within a repo_group`
    list all repos in repo_group="DMAI Push IPs"

    3. `Report drops(build_tag) for a given (domain/milestone)`
    list the  build_drops where domain="DV" and milestone="0.5" in a tabulated format. if there are multiple build_tag name from the same master_repo, only list the latest creation


## UML Diagram Of Aidash
https://altera-my.sharepoint.com/:b:/p/kenveng_ng/Ed_U-YnCBpRHgtapcgiODxoBk0ykMMlXqm90IuW9THy2Wg?e=YTBNbz
    """
    gu.print_markdown(text, cursor_moveback=False)
    
 

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='ask.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-q', '--query', default=None, help='Query string')
    parser.add_argument('-y', '--yes', default=False, action='store_true', help='Answer "y" to all questions')
    
    parser.add_argument('-u', '--userguide', default=False, action='store_true', help='Show user guide')

    args = parser.parse_args()

    main(args)

