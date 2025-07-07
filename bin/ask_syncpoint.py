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

    a = SqlCodingAgent()
    a.cnffile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sql_cnf_files', 'syncpoint.cnf'))
    a.tables = ['syncpoint_syncpoint', 'syncpoint_release'] 
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]
    res = a.run()
    fullres = ''
    print('----------------------------------------')

    sqlrawcmd = res.message['content']
    output = a.execute_sql(sqlrawcmd)

    b = BaseAgent()
    b.kwargs['model'] = 'llama3.3'
    b.kwargs['stream'] = True 
    b.kwargs['options']['num_ctx'] = 36000
    b.kwargs['options']['temperature'] = 0.3
    b.kwargs['options']['top_p'] = 0.3
    b.systemprompt = ''
    b.kwargs['messages'] = [{'role': 'user', 'content': f'''
        The user asked: {args.query}   

        The SQL query command ran: {sqlrawcmd}  

        The SQL query returned the following results:  {output}  

        By using all these provided info, help answer the user's original query.   
        Output every single item of data in the results, without any truncation or ellipsis.  
        Report the results in a properly formatted tabular format, if possible.   
        Generate the entire response in markdown format.  


    '''}]
    LOGGER.debug(b.kwargs['messages'])
    res = b.run()
    ani.stop()
    fullres = ''
    for chunk in res:
        print(chunk['message']['content'], end='', flush=True)
        fullres += chunk['message']['content']
        
    
    print()
    print("==================================================================")
    import tempfile
    print("==================================================================")
    print("==================================================================")
    print("==================================================================")
    print("==================================================================")
    print(f"Question: {args.query}")
    print("==================================================================")
    pyg_exe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/pygmentize'
    with tempfile.NamedTemporaryFile(mode='w+t', delete=False) as temp_file:
        temp_file.write(fullres)
        cmd = f'''{pyg_exe} -l md {temp_file.name}'''
    if args.debug:
        print(f"cmd: {cmd}")
    os.system(cmd)

def get_create_table_statement(cnffile):
    tables = ['syncpoint_syncpoint', 'syncpoint_release']
    ret = ''
    for table in tables:
        cmd = f"mysql --defaults-file={cnffile} -e 'desc {table}'"
        cmd = f"mysql --defaults-file={cnffile} -se 'show create table {table}' | tail -n1"
        output = subprocess.getoutput(cmd)
        ret += f"\n\n**Create Table Statement: {table}**: {output}\n\n  "
    return ret


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='ask.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-q', '--query', default=None, help='Query string')

    args = parser.parse_args()

    main(args)

