#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Overview:
    This agent is used to 
    - run a given command
    - convert the command output into a (expected) json format.

Usage:
    from lib.agents.cmd2json_agent import Cmd2jsonAgent
    a = Cmd2jsonAgent()

    ### Override default settings, if needed
    a.kwargs['model'] = 'qwen2.5'
    a.kwargs['options']['top_p'] = 1.0
    a.kwargs['stream'] = False

    ### Provide required input
    a.cmd = 'ls -al'
    a.expected_json_format = '{"files": [<filename>, <filename>, ...], "directories":[<directoryname>, <firectoryname>, ...]}'
    res = a.run()
   
    data = res.message['content']
    print(json.dumps(json.loads(data), indent=4))
    
Example:
    For a full detail execution, please refer to the example in the end of this file, at
        if __name__ == '__main__':
    
'''
import os
import sys
import ollama
import logging
from pprint import pprint, pformat
import subprocess
import tempfile
import json
import re

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent



class Cmd2jsonAgent(BaseAgent):
    def __init__(self):
        super().__init__()
     
        ### llm settings for this agent
        self.kwargs['stream'] = False
        self.kwargs['options']['num_ctx'] = 11111
        self.kwargs['options']['temperature'] = 0.0
        self.kwargs['options']['top_p'] = 0.0
        self.emb_model = 'llama3.3'
        self.systemprompt = ''' You are an expert in converting a given info into json. Given User Data, you will convert the data into a json format. You will only return the json format, and nothing else.   You will not return any explanation, you will not return any markdown. You will not return any code block. You will only return the json format.   If Expected JSON format is provided, return the json format *strictly* according to the Expected JSON format only, nothing extra.   
        '''
        self.cmd = ''   # Command to run, that needs to be provided by caller.
        self.expected_json_format = {}  # To be provided by caller (optional)
        self.input_string = ''  # To be provided by caller (optional) If this is given, it will be used instead of self.cmd.

    def run_cmd(self):
        output = subprocess.getoutput(f'{self.cmd}')
        return output

    def run(self):
        if not self.input_string:
            self.cmd_output = self.run_cmd()
        else:
            self.cmd_output = self.input_string

        prompt = f'**User Data:** {self.cmd_output}'
        if self.expected_json_format:
            prompt += f'\n\n**Expected JSON format:** {self.expected_json_format}'

        kwargs = self.kwargs.copy()
        kwargs['messages'] = [
            {'role': 'system', 'content': self.systemprompt},
            {'role': 'user', 'content': prompt},
        ]
        self.logger.debug(pformat(kwargs))
        res = ollama.chat(**kwargs)
        return res


    def write_code_to_file(self, code):
        with open(self.codefile, 'w') as f:
            f.write(code)

    def print_code(self):
        cmd = f'''{self.pygmentize} -l py {self.codefile}'''
        os.system(cmd)
     
    def remove_markdown(self, code):
        code = re.sub(r"```[\w\s]*\n", '', code)
        code = re.sub(r"`", '', code)
        return code


if __name__ == '__main__':
    ### To run: 
    ###     >env OLLAMA_HOST=asccf06294100.sc.altera.com:11434 ./python_coding_agent.py
    logging.basicConfig(level=logging.DEBUG)

    a = Cmd2jsonAgent()
    a.cmd = sys.argv[1] 
    if len(sys.argv) > 2:
        a.expected_json_format = sys.argv[2]
    res = a.run()
    print('======================')
    print("cmd_output:")
    print('-----------------------')
    print(a.cmd_output)
    print('======================')
    print('======================')
    print('json:')
    print('-----------------------')
    data = res.message['content']
    print(json.dumps(json.loads(data), indent=4))
    print('======================')



