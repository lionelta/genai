#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''

======================================
## How to use ToolAgent
======================================
1.  Create a toolfile.py file that contains the functions you want to call.
2.  Set the toolfile attribute of the ToolAgent instance to the path of your toolfile.py file.
3.  Call the run() method of the ToolAgent instance to get the response.
4.  The response will be a list of return values from the functions called in the toolfile.py file.
    

======================================
## Code Example (ToolAgent):
======================================
    a = ToolAgent()
    a.toolfile = <path to toolfile.py>
    a.kwargs['messages'] = [{'role': 'user', 'content': <user query>}]
    response = a.run() 
    # Response(model='llama3.3' 
        created_at='2025-04-18T06:20:17.14553645Z' 
        done=True 
        done_reason='stop' 
        total_duration=12785807414 
        load_duration=8128787086 
        prompt_eval_count=917 
        prompt_eval_duration=2165000000 
        eval_count=34 
        eval_duration=1794000000 
        message=Message(role='assistant', 
            content='[
                {"function": "explain_code", "parameters": {"filelist": ["bin/ask.py"], "level": "high"}, "missing_params": []}
            ]', 
            images=None, 
            tool_calls=None
        )
    )
    
    # What you are interested should be only this: response.message['content']
    # You can now do whatever you want with the response. But if you would like to call the function in the toolfile.py, you can do it like this:
    outputs = a.execute_response(response)

    # outputs == [
        'stdout from function1',
        'stdout from function2',
        ... ... ...
    ]

    # If there is a missing parameter, the output will be:
    # outputs == [
        'missing_params: ["filelist"]',
        'stdout from function2',
        ... ... ...
    ]

======================================
## Toolfile.py Example:
======================================
    explain_code_dict = {
        'type': 'function',
        'function': {
            'name': 'explain_code',
            'description': 'explain the code of a given list of files, based on the given level.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'filelist': {
                        'type': 'list',
                        'description': 'The list of files to be explained',
                        'required': True,
                    },
                    'level': {
                        'type': 'string',
                        'description': 'The level of detail for the explanation, whereby high is the least detailed, mid is the medium detailed, and low is the most detailed.',
                        'choices': ['high', 'mid', 'low'],
                        'default': 'high',
                        'required': False,
                    }
                },
            },
        }
    }
    def explain_code(filelist='', level='high'):
        exe = os.path.join(rootdir, 'bin', 'explain_code.py')
        cmd = '{} -f {} -e {}'.format(exe, ' '.join(filelist), level)
        LOGGER.debug(f'Tool Ran: {cmd}')
        os.system(cmd)
    # --------------------------------------------------
    other_tool_dict = {
        'type': 'function',
        'function': {
            'name': 'other_tool',
            ...   ...   ...
    }       
    def other_tool():
        ... ... ...
    # --------------------------------------------------
    all_tools = [explain_code_dict, other_tool_dict]


======================================
## Real Examples:
======================================
ToolAgent usage: 
    bin/myhelper.py

toolfile.py:
    toolfiles/myhelper_toolfile.py


'''
import os
import sys
import re
import ollama
from pprint import pprint
import importlib
import json

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
from agents.base_agent import BaseAgent

class ToolAgent(BaseAgent):

    def __init__(self):
        super().__init__()

        self.systemprompt = ''

        ### Overriding default settings
        self.kwargs['stream'] = False
        self.kwargs['options']['top_p'] = 0.0
        self.kwargs['options']['temperature'] = 0.0
        #self.kwargs['format'] = 'json' # strangely, adding this returns a very wide json string

        self.toolfile = None


    def run(self):
        self.mytools = self.load_toolfile()
        #self.kwargs['tools'] = mytools.all_tools
        self.systemprompt = """You are an intelligent function calling system.
        Your task is to analyze user requests and determine the appropriate function to execute. 
        You will search for matching function based on the user's intent and available tools.

Your output must be in JSON string, adhering to the following structure:

* **If a matching function is found (with some required parameters not provided):**   
{"function": "name_of_the_function", "parameters": {"parameter1": "value1", "parameter2": "value2", ...}, "missing_params": ["parameter3", "parameter4", ...]}
  
  
* **If a matching function is found (with all required parameters provided):**
{"function": "name_of_the_function", "parameters": {"parameter1": "value1", "parameter2": "value2", ...}, "missing_params": []}
  
  
* **If a matching function(with no required parameters) is found:**
{"function": "name_of_the_function", "parameters": {}, "missing_params": []}
  
  
* **If no matching function found:**
{}
  
  
**Instructions:**

1.  **Understand the User Request:** Carefully analyze the user's input to determine their intent.
2.  **Function Matching:** Compare the user's intent with the available functions.
3.  **Parameter Extraction:** If a matching function is found, extract the necessary parameters from the user's input.
4.  **JSON Output:** Format your response strictly as a JSON string, following the specified structure. Do not format the response using markdown or triple backticks. Return it as plain text. 
5.  **No Explanations:** Do not provide any additional explanations or conversational responses. Only return the JSON output.

**Available Functions:**
""" + json.dumps(self.mytools.all_tools)

        res = super().run()
        return res


    def execute_response(self, res):
        ''' res = response returned from self.run() 
        
        res.message: Message(role='assistant', 
        content='[{
            "function": "explain_code", 
            "parameters": {"filelist": ["./bin/ask.py", "./bin/explain_code.py", "./lib/agents/*.py"]}, 
            "missing_params": []
        }]'

        return = ''
        '''
        ret = ''
        try:
            data = json.loads(self.remove_markdown(res.message.content))
            ret = getattr(self.mytools, data['function'])(**data['parameters'])
        except Exception as e:
            ret = str(e)

        return ret

    # alias for execute_response
    call_tool = execute_response

    def is_function_name_in_loaded_tools(self, function_name):
        '''Check if the function name is in the loaded tools.'''
        loaded_tools = self.load_toolfile()
        for tool in loaded_tools.all_tools:
            if tool['function']['name'] == function_name:
                return True
        return False


    def get_called_tools(self, res):
        '''Get the data of all the tools called in the response.'''
        try:
            data = json.loads(self.remove_markdown(res.message.content))
            if 'function' in data and 'parameters' in data:
                return data
        except Exception as e:
            pass
        return []


    def load_toolfile(self):
        ''' mytools = [
        {
            'type': 'function', 
            'function': {
                'name': 'add', 
                'description': 'add two numbers', 
                'parameters': {
                    'type': 'object', 
                    'properties': {
                        'a': {
                            'type': 'int', 
                            'description': 'The first number to add', 
                            'required': True}, 
                        'b': {
                            'type': 'int', 
                            'description': 'The second number to add', 
                            'required': True}
                    }
                }
            }
        },
        ...   ...   ...
        '''
        spec = importlib.util.spec_from_file_location("module.mytools", self.toolfile)
        mytools = importlib.util.module_from_spec(spec)
        sys.modules['module.mytools'] = mytools
        spec.loader.exec_module(mytools)
        return mytools


    def remove_markdown(self, code):
        code = re.sub(r"```[\w\s]*\n", '', code)
        code = re.sub(r"`", '', code)
        return code


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    os.environ['OLLAMA_HOST'] = 'asccf06294100.sc.altera.com:11434'
    a = ToolAgent()
    a.toolfile = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/toolfile_example.py'
    a.kwargs['messages'] = [
        {'role': 'user', 'content': 'what are the tasks that you can do?'},
    ]
    res = a.run()

    pprint(res)
