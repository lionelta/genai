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


rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']
import ollama

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.tool_agent import ToolAgent
from lib.loading_animation import LoadingAnimation

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'


class PlannerAgent(ToolAgent):

    def __init__(self):
        super().__init__()
        self.toolfile = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/toolfiles/generic_toolfile.py'

    def run(self):
        self.mytools = self.load_toolfile()
        self.systemprompt = """
You are a highly capable AI task orchestrator. Think step by step. Your role is to analyze complex user requests and decompose them into a sequence of general actions, without predicting the specific subtasks or tools required to fulfill each action. You have access to a diverse set of tools and agents, each specialized in a particular domain. Your goal is to create an execution plan that outlines the necessary high-level steps to achieve the user's objective, enabling flexible execution by downstream systems.

Focus on the overall flow and dependencies between actions, rather than diving into the specifics of how each action will be carried out.  Avoid making assumptions about the capabilities or limitations of specific tools or agents.

Analyze this task and break it down into smaller tasks.

Return your response in this format:  

<analysis>
Explain your understanding of the task and which variations would be valuable.  
Focus on how each approach serves different aspects of the task.
</analysis>

<tasks>
    <task>
        <agent>agent to call</agent>
        <prompt>prompt to be provided to agent</prompt>   
    </task>
    <task>
        <agent>agent to call</agent>
        <prompt>prompt to be provided to agent</prompt>   
    </task>
    ... ... ...
</tasks>


**Here are the Available Agents/Functions that you can use:**
""" + json.dumps(self.mytools.all_tools)

        self.kwargs['messages'].insert(0, {'role': 'system', 'content': self.systemprompt})
        self.logger.debug(pformat(self.kwargs))
        res = ollama.chat(**self.kwargs)
        return res


def parse_tasks(tasks_xml):
    tasks = []
    task_list = re.findall(r'<task>(.*?)</task>', tasks_xml, re.DOTALL)
    for task in task_list:
        agent = re.search(r'<agent>(.*?)</agent>', task).group(1)
        prompt = re.search(r'<prompt>(.*?)</prompt>', task).group(1)
        tasks.append({'agent': agent, 'prompt': prompt})
    return tasks


def main(args):

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)


    ### Planner Agent
    a = PlannerAgent()
    a.toolfile = os.path.join(rootdir, 'toolfiles', 'generic_toolfile.py')
    a.kwargs['messages'] = [{'role': 'user', 'content': "**User Request:** " + args.query}]
    
    ### Print out all the toolfile loaded agents
    if args.debug:
        print("These are all the available tools:")
        tf = a.load_toolfile()
        tf.print_all_tools()
   
    import loading_animation
    ani = loading_animation.LoadingAnimation()
    ani.run(text='')
    res = a.run()
    ani.stop()
    planner_raw = res.message['content']
    analysis = gu.extract_xml(planner_raw, 'analysis')
    tasks_xml = gu.extract_xml(planner_raw, 'tasks')
    tasks = parse_tasks(tasks_xml)
    print()
    print("\n=== ORCHESTRATOR OUTPUT ===")
    print(f"\nANALYSIS:\n{analysis}")
    print(f"\nTASKS:\n{json.dumps(tasks, indent=2)}")



    sys.exit()




if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='myhelper.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-q', '--query', default=None, help='Query string')
    args = parser.parse_args()

    main(args)

