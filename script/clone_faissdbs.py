#!/usr/intel/pkgs/python3/3.11.1/bin/python3

'''
$Heaidar: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/syncpoint.py#1 $

Description:  AIDE: Altera Integrated Data Exchange 

Copyright (c) Altera Corporation 2024
All rights reserved.
'''
import UsrIntel.R1
import sys
import os
import argparse
import logging
from pprint import pprint

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'


LOGGER = logging.getLogger()

def main():
    LOGGER.info('Starting the program')
    if len(sys.argv) < 3:
        print("""
            Usage: clone_faissdbs.py <from version> <to version>
            Example: clone_faissdbs.py main 25.100""")
        return 1

    source_version = sys.argv[1]
    target_version = sys.argv[2]
    basedir = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai'
    
    ### get_all_faissdbs_from_source
    ### store all found dbpath in a list like this:
    ### [ ['dbname1', 'dbpath1'], ['dbname2', 'dbpath2'] ]
    alldbs = []
    source_dir = os.path.join(basedir, source_version, 'faissdbs')
    for dbname in os.listdir(source_dir):
        dbpath = os.path.join(source_dir, dbname, 'default')
        if os.path.exists(dbpath):
            LOGGER.info(f'Found FAISS DB: {dbname} at {dbpath}')
            alldbs.append([dbname, dbpath])
        else:
            LOGGER.warning(f'FAISS DB: {dbname} not found at {dbpath}')

    pprint(alldbs)

    ### Create faissdb paths in target version
    target_dir = os.path.join(basedir, target_version, 'faissdbs')
    os.system(f'mkdir -p {target_dir}')
    LOGGER.info(f'Created target directory: {target_dir}')
    for dbname, source_dbpath in alldbs:
        target_dbname_path = os.path.join(target_dir, dbname)
        os.system(f'mkdir -p {target_dbname_path}')
        cmd = f'ln -s {source_dbpath} {target_dbname_path}/default'
        os.system(cmd)

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

