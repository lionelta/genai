#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md

Usage:
    
    from agents.base_agent import BaseAgent
    a = CodeExplainAgent()

    ### Override default settings
    a.kwargs['model'] = 'qwen2.5'
    a.kwargs['options']['top_p'] = 1.0
    a.kwargs['stream'] = False

    ### Provide the file to be explained
    a.codefile = <path to file>

    ### Provide the Explanation level (low=very detailed, mid=medium, high=very brief)
    a.explanation = 'low'

    res = a.run()
    if 'stream' in kwargs and kwargs['stream']:
        for chunk in res:
            print(chunk['message']['content'], end='', flush=True)
    else:
        pprint(res)
'''
import os
import sys
import ollama
import logging
from pprint import pprint, pformat

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import genai_utils
from lib.agents.base_agent import BaseAgent

class ExplainCodeAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.systemprompt = ''
        self.codefile = ''
        self.genai_utils = genai_utils
        self.default_settings = self.genai_utils.load_default_settings()
        self.kwargs = self.init_ollama_chat_kwargs()    # ollama chat kwargs
        self.explainmode = {
            'low': """Provide a comprehensive, line-by-line explanation of the code's functionality. Describe the data structures, control flow, algorithms, and any relevant programming concepts involved. Explain the purpose of each variable, the logic within loops and conditional statements (if any), and the return values of functions.""",
            'mid': """Explain the code's main purpose and how it achieves it. Describe the key components and their roles in the process. Avoid deep technical jargon but use basic programming terminology.""",
            'high': """Provide a concise explanation of what the code does overall, without going into any programming specifics."""
        }
        

    def run(self):
        kwargs = self.kwargs.copy()
        self.systemprompt = f"You are a code explainer. You will be given a code snippet. {self.explainmode[self.explanation]}."
        self.kwargs['messages'] = [{'role': 'user', 'content': self.get_code_from_file()}]
        self.logger.debug(pformat(self.kwargs))
        res = super().run()
        return res

    def init_ollama_chat_kwargs(self):
        ''' https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion '''
        settings = {}
        settings['model'] = self.default_settings['llm_model']
        settings['options'] = {}
        settings['options']['top_p'] = self.default_settings['top_p']
        settings['options']['temperature'] = self.default_settings['temperature']
        settings['options']['num_ctx'] = 8192
        return settings

    def get_code_from_file(self):
        if not os.path.isfile(self.codefile):
            code = f"File {self.codefile} does not exist."
        with open(self.codefile, 'r') as file:
            code = file.read()
        return code


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    kwargs = {
        'stream':False 
    }
    a = BaseAgent()
    a.kwargs['messages'] = [
        {'role': 'user', 'content': 'what is the capital of France?'},
        {'role': 'assistant', 'content': 'The capital of France is Paris.'},
        {'role': 'user', 'content': 'what about India?'}
    ] 
    a.kwargs['stream'] = False
    res = a.run()
    if 'stream' in a.kwargs and a.kwargs['stream']:
        for chunk in res:
            print(chunk['message']['content'], end='', flush=True)
    else:
        pprint(res)
