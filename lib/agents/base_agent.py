#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md

Usage:
    
    from agents.base_agent import BaseAgent
    a = BaseAgent()

    ### Override default settings
    a.kwargs['model'] = 'qwen2.5'
    a.kwargs['options']['top_p'] = 1.0
    a.kwargs['stream'] = False

    ### Provide system prompt (Instruction to LLM)
    a.systemprompt = 'You are a helpful and informative assistant. You will be provided with several chunks of information retrieved from various web pages.  These chunks are related to a user\'s query and are intended to provide context for your response.  **You MUST ONLY use the information provided in these chunks to answer the user\'s question.** Do not use any other knowledge or information.'

    ### Provide user qeury (with chat history)
    a.kwargs['messages'] = [
        {'role': 'user', 'content': 'what is the capital of France?'},
        {'role': 'assistant', 'content': 'The capital of France is Paris.'},
        {'role': 'user', 'content': 'what about India?'}
    ]

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
import lib.chat_factory.factory
import lib.usagelog

class BaseAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.systemprompt = ''
        self.genai_utils = genai_utils
        self.default_settings = self.genai_utils.load_default_settings()
        self.kwargs = self.init_ollama_chat_kwargs()    # ollama chat kwargs

        self.chat_factory = lib.chat_factory.factory.Factory().get_chat_factory()

    def run(self):
        kwargs = self.kwargs.copy()
        if hasattr(self, 'systemprompt') and self.systemprompt:
            kwargs['messages'].insert(0, {'role': 'system', 'content': self.systemprompt})
        self.logger.debug(pformat(kwargs))

        res = self.chat_factory.chat(kwargs)
        lib.usagelog.UsageLog().write_log(f'/nfs/site/disks/da_scratch_1/users/yltan/genailogs/{os.getenv("EC_SITE")}/base_agent/', kwargs['messages'])
        return res


    def init_ollama_chat_kwargs(self):
        ''' https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion '''
        settings = {}
        settings['model'] = self.default_settings['llm_model']
        settings['options'] = {}
        settings['options']['top_p'] = self.default_settings['top_p']
        settings['options']['temperature'] = self.default_settings['temperature']
        settings['options']['num_ctx'] = 8192
        if 'seed' in self.default_settings:
            settings['options']['seed'] = self.default_settings['seed']
        return settings


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
