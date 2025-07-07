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

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

LOGGER = logging.getLogger()

class OllamaChatFactory:
    def __init__(self):
        pass

    def chat(self, ollama_kwargs):
        import ollama
        response = ollama.chat(**ollama_kwargs)

        if 'stream' not in ollama_kwargs or not ollama_kwargs['stream']:
            return response
        else:
            return self.stream_generator(response)

    def stream_generator(self, response):
        for chunk in response:
            yield chunk.message.content

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

