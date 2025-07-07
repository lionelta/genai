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

class Factory:
    def __init__(self):
        pass

    def get_chat_factory(self):
        api_key = self.get_azure_openai_key()
        if api_key:
            from lib.chat_factory.openai_factory import OpenaiChatFactory
            self.chat_factory = OpenaiChatFactory(api_key)
        else:
            from lib.chat_factory.ollama_factory import OllamaChatFactory
            self.chat_factory = OllamaChatFactory()
        return self.chat_factory

    def get_azure_openai_key(self):
        if 'AZURE_OPENAI_API_KEY' in os.environ:
            return os.environ['AZURE_OPENAI_API_KEY']
        return False

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)

