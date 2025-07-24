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
import base64

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

os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
os.environ['AZURE_OPENAI_MODEL'] = 'gpt-4o'

def main(args):
    if args.debug:
        pprint(args)

    LOGGER = logging.getLogger()
    level = logging.INFO
    if args.clean:
        level = logging.WARNING # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    LOGGER.setLevel(level)
    
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s-[%(pathname)s:%(lineno)d]: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

    a = ChatbotAgent()
    prompt = args.query + '  \n\n'
    if args.pipe:
        prompt += sys.stdin.read()
   
    if args.snap:
        if args.loaddb or args.spaces:
            print("ERROR: The --snap option does not work with --loaddb or --spaces options. Please remove them.")
            return

        _, image_path = tempfile.mkstemp(suffix='.jpeg')
        print(">>> Please draw a box around the error message you want to extract...")   
        cmd = f'import {image_path}'
        os.system(cmd)
        print(f">>> Image captured: {image_path}")
        base64_image = get_base64_image(image_path)

        a.kwargs['messages'] = [
            {"role": "user", "content": [{"type": "image_url", "image_url":{ "url": f"data:image/png;base64,{base64_image}"}}]},
            {"role": "user", "content": prompt}
        ]
    else: 
        a.kwargs['messages'] = [{'role': 'user', 'content': prompt}]

    a.faiss_dbs = []
    if args.loaddb:
        a.faiss_dbs = args.loaddb

    ### Load the FAISS dbs thru spaces
    if args.spaces:
        for space in args.spaces:
            dbpath = os.path.join('/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs', space, 'default')
            if os.path.exists(dbpath):
                a.faiss_dbs.append(dbpath)
            else:
                LOGGER.warning(f"Space {space} does not exist. Skipping.")
    
    ### Uniqifying the FAISS dbs
    a.faiss_dbs = list(set(a.faiss_dbs))

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


def get_base64_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    epilog = f'''
================
Example usage:
================

    Generic Question
    ---------------- 
    {os.path.basename(__file__)} -q "What is the meaning of life?"

    Internal Question(with faissdb knowledge)
    ------------------------------------------------
    {os.path.basename(__file__)} -l my_faiss_db -q "how to resolve error W154?"
    {os.path.basename(__file__)} --spaces dmx_km_be -q "explain how to use dmx report bloodline?"

    Query With Pipeline
    ------------------------------------------------ 
    cat test.py | {os.path.basename(__file__)} --pipe -q 'explain what this python code does'
    ls -altr | {os.path.basename(__file__)} --pipe -q 'convert this output to json string. Do not provide any explanation, just the json string.'

    Query With Snapshot
    ------------------------------------------------
    {os.path.basename(__file__)} --snap -q 'What is the error in this image? Please provide a detailed explanation and solution.'
    ### Please draw a box around the error message you want to extract...

'''
    parser = argparse.ArgumentParser(prog='ask.py', epilog=epilog, formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('--clean', action='store_true', default=True, help='Clean mode')
    
    parser.add_argument('-l', '--loaddb', default=None, nargs='+', help='Load the FAISS db')
    parser.add_argument('--spaces', default=None, nargs='+', help='Spaces to load the FAISS db from.')
    parser.add_argument('-q', '--query', default=None, required=True, help='Query string.')
    parser.add_argument('--pipe', action='store_true', default=False, help='Will read from stdin and pipe/append the output to the query.')
    parser.add_argument('--snap', action='store_true', default=False, help='Will take a snapshot of from a user defined box and append it to the query. (Currently only works without --loaddb and --spaces options)')

    parser.add_argument('-sm', '--scripting_mode', action='store_true', default=False, help='Will print response in non-streaming mode. Useful for scripting.')
    args = parser.parse_args()

    main(args)

