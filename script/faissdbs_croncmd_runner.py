#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
$Headar: //depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/bin/syncpoint.py#1 $

Description: This script is used to run the faissdbs cron command
It will search for all the faissdbs in:
        $rootdir/faissdbs/<space>/default
... and if there is a `.croncmd` file in the directory, it will run the command in the file.

'''
import sys
import os
import argparse
import logging
from pprint import pprint

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

ROOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOTDIR)
import lib.genai_utils as gu

LOGGER = logging.getLogger()

def main(args):
    LOGGER.info('Starting the program')
    dbpaths = gu.get_faiss_dbs(args.rootdir)   
    for space in dbpaths:
        LOGGER.info(f'Processing {space}')
        
        if args.spaces and space not in args.spaces:
            LOGGER.info(f'Skipping {space} because it is not the specified space: {args.spaces}')
            continue

        croncmd = os.path.join(os.path.realpath(dbpaths[space]['dbpath']), '.croncmd')
        if os.path.exists(croncmd):
            LOGGER.info(f'.croncmd file found: {croncmd}')

            ### Get email list
            emails = ''
            emailsfile = os.path.join(os.path.realpath(dbpaths[space]['dbpath']), '.emails')
            if os.path.exists(emailsfile):
                with open(emailsfile, 'r') as f:
                    emails = f.read().strip()
                    LOGGER.info(f'.emails file found: {emails}')
            emails = emails + ',lionelta'

            ### Submit job to farm
            cmd = f"""{croncmd} ; cat $ARC_JOB_STORAGE/std*.txt | mail -s "WEEKLY-FAISSDB-UPDATE: ({space}) completed. ($ARC_JOB_ID)" {emails}"""
            arccmd = f"""/p/psg/ctools/arc/bin/arc submit --watch mem=12000 -- '{cmd}' """
            LOGGER.info(f'Running arc command: {arccmd}')
            os.system(arccmd)
        else:
            LOGGER.info(f'.croncmd file not found: {croncmd}')


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    parser = argparse.ArgumentParser(prog='faissdbs_croncmd_runner.py')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-r', '--rootdir', default='', required=True, help='root directory that contains the faissdbs')

    parser.add_argument('-s', '--spaces', default=None, nargs='*', required=False, help='If this is given, only the spaces will be processed')

    args = parser.parse_args()
    
    sys.exit(main(args))

