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

threads = {}

def main(args):
    global threads

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)


    errors = extract_errors_from_logfile(args.logfile)
    print(f'Total Of {len(errors)} errors found')
    print(f"Generating explanation file for {args.logfile}...")
    #ani = LoadingAnimation()

    process_queries_in_parallel(errors)

    with open(args.outputfile, 'w') as f:
        threads_id = sorted([int(x) for x in threads.keys()])
        for i in threads_id:
            tid = str(i)
            thread = threads[tid]
            f.write("===============================================================================\n")
            f.write("===============================================================================\n")
            f.write(f"Error #{tid}\n")
            f.write("===============================================================================\n")
            f.write(f"{thread['query']}\n")
            f.write("-------------------------------------------------------------------------------\n")

            f.write(thread['ret'])
            f.write("\n\n")

    print(f"Explanation file {args.outputfile} generated.")

def process_queries_in_parallel(queries):
    global threads

    for tid, query in enumerate(queries):
        thread_id = str(tid + 1)
        t = threading.Thread(target=process_query, kwargs={'query': query, 'tid': thread_id})
        threads[thread_id] = {'thread': t, 'ret': '', 'query': query}

    ### only run 4 threads at a time
    max_parallel_jobs = 10

    ### Starting threads
    submitted = 0
    for tid in threads:
        thread = threads[tid]['thread']
        while get_current_running_jobs() >= max_parallel_jobs:
            print(f'Max Parallel Jobs({max_parallel_jobs}) met. Waiting for threads to finish ...')
            print(f' - Total Jobs: {len(queries)}, Submitted: {submitted}')
            time.sleep(10)
        thread.start()
        submitted += 1

    for t in threads:
        thread = threads[t]['thread']
        thread.join()


def process_query(query='', tid=''):
    print(f'    > Starting thread {tid}')
    agent = VcsDebuggerAgent()
    agent.error_message = query
    response = agent.run()
    threads[tid]['ret'] = response.message['content']
    print(f'    > Completed thread {tid}')


def get_current_running_jobs():
    global threads
    running_jobs = 0
    for t in threads:
        thread = threads[t]['thread']
        if thread.is_alive():
            running_jobs += 1
    return running_jobs

def extract_errors_from_logfile(logfile):
    with open(logfile, 'r') as f:
        start = False
        error = ''
        errors = []
        for line in f:
            if not start:
                if line.startswith('Error-'):
                    start = True
                    error += line
                    continue
            else:
                if line.isspace():
                    start = False
                    errors.append(error)
                    error = ''
                    continue
                else:
                    error += line
                    continue
    return errors


class VcsDebuggerAgent(BaseAgent):
    def __init__(self):
        super().__init__()

        self.systemprompt = """
        You are an expert in VCS (Verilog Compiler Simulator).
        You will be given a VCS related error message.
        Your task is to provide a detailed explanation of each error, including the possible causes and solutions.
        Your response should be in the following format:

        [EXPLANATION]
        detail explanation of the error ...

        [SOLUTION]
        detail solution of the error ...
        """

        self.error_message = ''

    def run(self):
        self.kwargs['messages'] = [{'role': 'user', 'content': f'**Error Message**: {self.error_message}'}]
        return super().run()

        

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='debug_vcs_errors.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    
    parser.add_argument('-t', '--threads', default=5, help='number of threads to run parallely', required=True)
    parser.add_argument('-l', '--logfile', default=None, help='input (error) logfile', required=True)
    parser.add_argument('-o', '--outputfile', default=None, help='output (explanation) file', required=True)

    args = parser.parse_args()

    main(args)

