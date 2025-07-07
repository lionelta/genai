#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md

Usage:
    
    from lib.agents.sql_coding_agent import PythonCodingAgent
    a = PythonCodingAgent()

    ### Override default settings, if needed
    a.kwargs['model'] = 'qwen2.5'
    a.kwargs['options']['top_p'] = 1.0
    a.kwargs['stream'] = False
    a.pythonexe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python'    # If you need to use your own python executable, set it here

    ### Provide required input
    a.kwargs['messages'] = [{'role': 'user', 'content': <user query>}]
    res = a.run()
    
    ### if you want to execute the python command
    pythoncode = res.message['content']
    output = a.execute_python(pythoncode)

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



class PythonCodingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
     
        self.pythonexe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python'
        self.codefile = tempfile.mkstemp(suffix='.py')[1]
        self.pygmentize = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/pygmentize'

        ### llm settings for this agent
        self.kwargs['stream'] = False
        self.kwargs['options']['num_ctx'] = 11111
        self.kwargs['options']['temperature'] = 0.0
        self.kwargs['options']['top_p'] = 0.0
        self.emb_model = 'llama3.3'
        self.systemprompt = '''You are a programming expert in python. Help generate Python scripts based on user requests.   
        You will not give me any other information or explanation. You will only give me the Python scripts.  
        Do not give me any explanation or any other information. Just give me the Python code in plain text.
        Do not format the Python code using markdown or triple backticks. Return it as plain text.   

        '''

    def execute_code(self, systemcall=False):
        """
        Execute the python code in the codefile.
        If systemcall is True, it will use os.system to execute the code.
        If systemcall is False, it will use subprocess.getoutput to execute the code and return the output.
        """
        cmd = f'{self.pythonexe} {self.codefile}'
        if not systemcall:
            output = subprocess.getoutput(cmd)
            return output
        else:
            return os.system(cmd)

    def run(self):
        kwargs = self.kwargs.copy()
        kwargs['messages'].insert(0, {'role': 'system', 'content': self.systemprompt})
        self.logger.debug(pformat(kwargs))
        #res = ollama.chat(**kwargs)
        res = super().run()
        code = res.message.content
        cleancode = self.remove_markdown(code)
        self.write_code_to_file(cleancode)
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

    ### Create temp csv file
    csvfile = tempfile.mkstemp(suffix='.csv')
    with open(csvfile[1], 'w') as f:
        for r in range(5):
            for c in range(5):
                f.write(f'r{r}c{c},')
            f.write('\n')
    
    a = PythonCodingAgent()
    a.kwargs['stream'] = False
    query = f'''help me extract out a csv file data({csvfile}). For all the rows, get the data from column 3 and 5, and return me the result in a json format that looks like this {{"row 1 column 3": <row 1 column 3 data>, "row 1 column 5": <row 1 column 5 data>, "row 2 column 3": <row 2 column 3 data>, ...}}. '''
    a.kwargs['messages'] = [
        {'role': 'user', 'content': query}, 
    ] 
    a.kwargs['stream'] = False
    res = a.run()
    pprint(res)
    pythoncode = res.message['content']
    print('======================')
    print('Python code:')
    print(res.message['content'])
    print('======================')

    ### execute the python code
    print('======================')
    print('Executing python code:')
    output = a.execute_code(pythoncode)
    pprint(json.loads(output))
    print('======================')


