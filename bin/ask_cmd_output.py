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
import tempfile
import subprocess

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
import lib.loading_animation

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.chatbot_agent import ChatbotAgent

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main(args):
    if args.debug:
        pprint(args)

    if args.userguide:
        print_user_guide()
        return

    LOGGER = logging.getLogger()
    level = logging.INFO
    level = logging.CRITICAL # suppress all logs, by default
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    a = ChatbotAgent()
    
    status, output = subprocess.getstatusoutput(args.cmd)
    
    a.kwargs['messages'] = [
        {'role': 'system', 'content': """You are a helpful assistant that can answer questions based on a given RAG content."""},
        {'role': 'user', 'content': f"""Help answer the User Query based on the given RAG Content.   

        **RAG Content:**{output}   

        **User Query:** {args.query}   

        """}
    ]
    

    if args.scripting_mode:
        a.kwargs['stream'] = False
        res = a.run()
        print(res.message.content)
        return


    ani = lib.loading_animation.LoadingAnimation()
    ani.run()
    res = a.run()
    ani.stop()
    time.sleep(1)
    fullres = ''
    for chunk in res:
        print(chunk, end='', flush=True)
        fullres += chunk

    time.sleep(1)   # wait for the last chunk to finish
    print()
    print('==================================================')
    print("(Markdown format)")
    print('--------------------------------------------------')
    gu.print_markdown(fullres, cursor_moveback=False)


def print_user_guide():
    exe = os.path.basename(sys.argv[0])
    text = f"""

## Here are a few useful prompting examples to get you started:

1. **Summarize The Content Of A File**
> {exe} -q "Summarize the data" --cmd 'cat <path_to_file>'

2. **Explain A python file**
> {exe} -q "Explain this python code" --cmd 'cat <path_to_python_file>'

3. **Re-Format Output To Certain Format**
> {exe} -q "Reformat the output to JSON string" --cmd 'ls -al'
    """
    gu.print_markdown(text, cursor_moveback=False)



if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='ask.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-ug', '--userguide', action='store_true', default=False, help='Print User Guide')
    
    parser.add_argument('-q', '--query', default=None, help='Query string. If "-" is provided, will read from stdin.')
    parser.add_argument('--cmd', default=None, help='Command to be executed.')

    parser.add_argument('-sm', '--scripting_mode', action='store_true', default=False, help='Will print response in non-streaming mode. Useful for scripting.')
    args = parser.parse_args()

    main(args)

