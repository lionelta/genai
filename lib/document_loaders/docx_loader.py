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
import base64
import subprocess
import json
import re
from pprint import pprint
import glob

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, rootdir)

import lib.genai_utils as gu
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader

class DocxLoader():

    def __init__(self):
        self.logger = logging.getLogger()

        self.markitdown_exe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/markitdown'

        self.savedir = ''   # REQUIRED: path to save all the files
        self.docxfile = ''  # REQUIRED

    def load(self):
        # 1. convert docx to markdown using markitdown
        outdir = os.path.realpath(self.outdir())
        os.system(f"mkdir -p {outdir}")
        outfile = os.path.join(outdir, 'converted.md')
        infile = os.path.realpath(self.docxfile)
        cmd = f'cd {outdir}; {self.markitdown_exe} {infile} -o {outfile}'
        os.system(cmd)
        documents = TextLoader(outfile).load()
        # chmod everything under self.savedir to 775
        try:
            os.system(f'chmod -R 775 {self.savedir}')
        except:
            pass
        return documents

    def outdir(self):
        return os.path.join(self.savedir, 'artifacts')

    def imgdir(self):
        return os.path.realpath(os.path.join(self.outdir(), 'images'))

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

