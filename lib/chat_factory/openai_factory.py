#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
$Heaidar: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/syncpoint.py#1 $

Description:  AIDE: Altera Integrated Data Exchange 

Copyright (c) Altera Corporation 2024
All rights reserved.
'''

import sys
import os
import argparse
import logging
import subprocess

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

LOGGER = logging.getLogger()

class OpenaiChatFactory:
    def __init__(self, api_key):
        self.api_key = api_key

    def chat(self, ollama_kwargs):
        from openai import AzureOpenAI
        kwargs = self.convert_ollama_kwargs_to_openai(ollama_kwargs)
        client = self.get_azure_openai_client()
        response = client.chat.completions.create(**kwargs)

        if 'stream' not in kwargs or not kwargs['stream']:
            return self.convert_openai_response_to_ollama(response)
        else:
            return self.stream_generator(response)


    def stream_generator(self, response):
        for chunk in response:
            try:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
            except:
                pass

    def get_azure_openai_key(self):
        cmd = '/p/psg/da/infra/admin/setuid/goak'
        return subprocess.getoutput(cmd)

    def convert_ollama_kwargs_to_openai(self, kwargs):
        openai_kwargs = {}

        ### if AZURE_OPENAI_MODEL is set, use that model
        ### otherwise, use the model specified in kwargs['model']
        ### but if the model does not start with 'gpt', default to 'gpt-4.1-nano'
        #openai_kwargs['model'] = 'gpt-4o'
        #openai_kwargs['model'] = 'gpt-4.1-nano'
        model = kwargs['model']
        if not model.startswith('gpt'):
            model = 'gpt-4.1-nano'
        openai_kwargs['model'] = os.environ.get('AZURE_OPENAI_MODEL', model)

        openai_kwargs['messages'] = kwargs['messages']
        if 'stream' in kwargs:
            openai_kwargs['stream'] = kwargs['stream']
        if 'options' in kwargs:
            if 'top_p' in kwargs['options']:
                openai_kwargs['top_p'] = kwargs['options']['top_p']
            if 'temperature' in kwargs['options']:
                openai_kwargs['temperature'] = kwargs['options']['temperature']
            if 'seed' in kwargs['options']:
                openai_kwargs['seed'] = kwargs['options']['seed']
        return openai_kwargs


    def get_azure_openai_client(self):
        from openai import AzureOpenAI
        import httpx
        proxy_client = httpx.Client(proxy='http://proxy-dmz.altera.com:912')
        client = AzureOpenAI(
            api_version = '2024-12-01-preview',
            azure_endpoint = "https://dmai-aichatbot.openai.azure.com/",
            api_key = self.get_azure_openai_key(),
            http_client = proxy_client,
        )
        return client


    def convert_openai_response_to_ollama(self, response):
        ''' Convert OpenAI response to Ollama response format '''
        if hasattr(response, 'choices') and len(response.choices) > 0:
            response = response.choices[0]
        return response


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

