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
import hashlib

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, rootdir)

import lib.genai_utils as gu
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader

class MsftxLoader():

    def __init__(self):
        self.logger = logging.getLogger()

        self.markitdown_exe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/markitdown'
        #self.pptx2md_exe = '/nfs/site/disks/da_scratch_1/users/pitlow/gitrepo/joannelow-scripts/convert_msft_pdf/venv/bin/pptx2md'
        self.pptx2md_exe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.11.1_pptx2md/bin/pptx2md'

        self.savedir = ''   # REQUIRED: path to save all the files
        self.msftxfile = ''  # REQUIRED

    def load(self):
        # 1. convert docx to markdown using markitdown
        outdir = os.path.realpath(self.outdir())
        ext = os.path.splitext(self.msftxfile)[1].lower()
        if ext not in ['.docx', '.pptx']:
            self.logger.error(f'Unsupported file extension: {ext}')
            return []
        md_fn = os.path.basename(self.msftxfile).replace(ext, '.md')
        os.system(f"mkdir -p {outdir}")
        outfile = os.path.join(outdir, md_fn)
        infile = os.path.realpath(self.msftxfile)
        if ext == '.pptx':
            img_dir = self.imgdir()
            cmd = f'cd {outdir}; {self.pptx2md_exe} {infile} --output {outfile} --image-dir {self.imgdir()}'
        else:
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
        filename = os.path.basename(self.msftxfile)
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]  # Use first 8 chars
        return os.path.realpath(os.path.join(self.outdir(), f'images_{file_hash}'))

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

