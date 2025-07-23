#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import logging
import os
import argparse
import sys
import base64
import tempfile
sys.path.insert(0, '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main')
from lib.agents.base_agent import BaseAgent
import lib.genai_utils as utils


def main(args):

    level = logging.INFO
    if '--debug' in sys.argv:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

    _, image_path = tempfile.mkstemp(suffix='.jpeg')

    print(">>> Please draw a box around the error message you want to extract...")   
    cmd = f'import {image_path}'
    os.system(cmd)
    print(f">>> Image captured: {image_path}")
    base64_image = get_base64_image(image_path)

    ### Openai format
    prompt = f'''
    You are a helpful assistant. Please help extract out the error message from the image, and provide the response in these sections:   
    - Extracted error message  
    - Explanation of the error message  
    - How to resolve the error  

    '''
    if args.query:
        prompt = args.query

    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    os.environ['AZURE_OPENAI_MODEL'] = 'gpt-4o'
    a = BaseAgent()
    a.kwargs['messages'] = [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url":{ "url": f"data:image/png;base64,{base64_image}"}},
        ]
         }]
    print(">>> Waiting response from llm ...")
    res = a.run()
    print("======================")
    print(res.message.content)

    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
   

def get_base64_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == '__main__':
    epilog = '''
By default, if you do not specify any query, the script will use this default prompt: 

    You are a helpful assistant. Please help extract out the error message from the image, and provide the response in these sections:   
    - Extracted error message  
    - Explanation of the error message  
    - How to resolve the error  

If you want to specify your own query, you can use the -q or --query option:
'''
    parser = argparse.ArgumentParser(description='Snap and ask for help with error messages.', epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-q', '--query', type=str, required=False, default=None, help='Query to ask the agent')
    args = parser.parse_args()
    main(args)

