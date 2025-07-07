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
import textwrap

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.chatbot_agent import ChatbotAgent
from lib.agents.base_agent import BaseAgent

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

threads = {}
LOGGER = logging.getLogger()

def main(args):
    global threads

    level = logging.CRITICAL # to suppress all logs
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)


    prompts = parse_inputfile(args.inputfile)
    LOGGER.info(f'Total Of {len(prompts)} prompts found')
    LOGGER.info(f"Generating explanation file for {args.inputfile} ...")
    LOGGER.info(prompts)
    
    process_queries_in_parallel(prompts, args.threads)

    with open(args.outputfile, 'w') as f:
        for tid in threads:
            thread = threads[tid]
            f.write("===============================================================================\n")
            f.write("===============================================================================\n")
            f.write(f"[{tid}]\n")
            f.write("===============================================================================\n")
            f.write(f"Question: {thread['query']}\n")
            f.write("-------------------------------------------------------------------------------\n")
            f.write(f"Answer: {thread['ret']}\n")
            f.write("\n\n")

    LOGGER.info(f"Explanation file {args.outputfile} generated.")

def process_queries_in_parallel(queries, max_parallel_jobs):
    global threads

    for thread_id in queries:
        query = queries[thread_id]
        t = threading.Thread(target=process_query, kwargs={'query': query, 'tid': thread_id})
        threads[thread_id] = {'thread': t, 'ret': '', 'query': query}


    ### Starting threads
    submitted = 0
    for tid in threads:
        thread = threads[tid]['thread']
        while get_current_running_jobs() >= max_parallel_jobs:
            LOGGER.info(f'Max Parallel Jobs({max_parallel_jobs}) met. Waiting for threads to finish ...')
            LOGGER.info(f' - Total Jobs: {len(queries)}, Submitted: {submitted}')
            time.sleep(10)
        thread.start()
        submitted += 1

    for t in threads:
        thread = threads[t]['thread']
        thread.join()


def process_query(query='', tid=''):
    LOGGER.info(f'    > Starting thread [{tid}]')

    a = ChatbotAgent()
    a.kwargs['messages'] = [{'role': 'user', 'content': query}]
    a.kwargs['stream'] = False
    a.faiss_dbs = args.loaddb

    response = a.run()
    threads[tid]['ret'] = response.message.content
    LOGGER.info(f'    > Completed thread [{tid}]')


def get_current_running_jobs():
    global threads
    running_jobs = 0
    for t in threads:
        thread = threads[t]['thread']
        if thread.is_alive():
            running_jobs += 1
    return running_jobs


def parse_inputfile(inputfile):
    ''' inputfile format:
[111]
how to 
   set a flow
      to non-gating
[Q2]
I have error W154
How should i resolve it

[question 3]   
how can we submit turnin to gatekeeper?
    
    return = {
        '111': 'how to set a flow to non-gating',
        'Q2': 'I have error W154 How should i resolve it',
        'question 3': 'how can we submit turnin to gatekeeper?'
    }

    '''
    ret = {}
    with open(inputfile, 'r') as f:
        for line in f:
            sline = line.strip()
            if sline.startswith('[') and sline.endswith(']'):
                key = sline[1:-1].strip()
                ret[key] = ''
            else:
                ret[key] += line
    return ret


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    epilog = textwrap.dedent(f'''
    Example Of Input File:
    =====================
    [Q1]
    how to set a flow to non-gating?

    [Q2]
    I have error W154
    How should i resolve it
    
    [Q3]
    how can we submit turnin to gatekeeper?
''')

    parser = argparse.ArgumentParser(prog='ask_batch.py', formatter_class=MyFormatter, epilog=epilog)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-t', '--threads', default=3, type=int, help='number of threads to run parallely', required=False, choices=list(range(1, 6)))
    parser.add_argument('-i', '--inputfile', default=None, help='input (error) logfile', required=True)
    parser.add_argument('-o', '--outputfile', default=None, help='output (explanation) file', required=True)
    parser.add_argument('-l', '--loaddb', default=None, nargs='+', help='Load the FAISS dbs')

    args = parser.parse_args()

    main(args)

