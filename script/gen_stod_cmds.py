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
import subprocess
from pprint import pprint

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

DMXLIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python'
CMXLIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python'
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)

LOGGER = logging.getLogger()

def main():
    LOGGER.info('Starting the program')
    cmdlist = ['stod', 'stodalert', 'stodcache', 'stodconfig', 
               'stoddisk', 'stodmonitor', 'stodstatus', 'stodadmin',
               'stodadmin', 'stodbackup', 'stodconfig2', 'stodfs', 'stodrepl']
    for c in cmdlist:
        output = subprocess.getoutput(f'{c} --help')
        subcmds = get_subcmds(output, c)
        for subcmd in subcmds:
            helptext = subprocess.getoutput(f'{c} {subcmd} --help')
            helpdesc = f'{c} {subcmd}: {subcmds[subcmd]}'
            with open(f'./stodcmds/{c}_{subcmd}.txt', 'w') as f:
                f.write(helpdesc + '\n')
                f.write(helptext)


def get_subcmds(output, cmd):
    ''' return: {
        '<subcmd>': '<description>'
        ... ... ...
    }
    '''
    subcmds = {}

    for line in output.split('\n'):
        line = line.strip()
        if line.startswith(cmd):
            sline = line.split()
            subcmd = sline[1]
            subdesc = ' '.join(sline[3:])
            subcmds[subcmd] = subdesc
    return subcmds

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

