#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import logging
import os
import sys
import base64
import tempfile
import argparse
import subprocess
import json
from urllib.parse import urlencode
from pprint import pprint
rootdir = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main'
sys.path.insert(0, rootdir)
from lib.agents.base_agent import BaseAgent
import lib.genai_utils as gu


def main():

    LOGGER = logging.getLogger()
    level = logging.INFO
    if '--debug' in sys.argv:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

    faissdir = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/25.013/faissdbs'
    dbs = os.listdir(faissdir)

    for db in dbs:
        dbpath = os.path.join(faissdir, db, 'default')
        destpath = dbpath + '_baai_bge_m3'
        if os.path.isdir(dbpath):
            LOGGER.info('Processing db: %s', dbpath)
            if not os.path.exists(destpath):
                cmd = f'cp -rfL {dbpath} {destpath}'
                LOGGER.info(f' - Running command: {cmd}')
                os.system(cmd)
            else:
                LOGGER.warning('Destination directory already exists: %s', destpath)

        else:
            LOGGER.warning('Skipping %s, not a directory', db)
            continue
       
        ### Remove the old 'default' directory
        cmd = f'rm {dbpath}'
        LOGGER.info('Removed old default directory: %s', cmd)
        os.system(cmd)

        ### link new default_baai_bge_m3 directory to default
        cmd = f'ln -s {destpath} {dbpath}'
        LOGGER.info('Linking new default directory: %s', cmd)
        os.system(cmd)


if __name__ == '__main__':

    main()

