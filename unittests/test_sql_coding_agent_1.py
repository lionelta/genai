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
from pprint import pprint
import json
os.environ['OLLAMA_HOST'] = 'asccf06294100.sc.altera.com:11434'

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

DMXLIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python'
CMXLIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python'
AILIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/'
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)
sys.path.insert(0, AILIB)
import lib.agents.sql_coding_agent

LOGGER = logging.getLogger()

def main():
    LOGGER.info('Starting the program')
    a = lib.agents.sql_coding_agent.SqlCodingAgent()
    a.cnffile = os.path.join(os.path.dirname(__file__), '..', 'sql_cnf_files', 'syncpoint.cnf')
    a.tables = ['syncpoint_syncpoint', 'syncpoint_release']
    query = f''' List out all syncpoint name which matches "FM4"   
    '''

    a.kwargs['messages'] = [{'role': 'user', 'content': query}]
    res = a.run()
    code = res.message['content']
    print("==========================================")
    print(code)
    print("==========================================")
    output = a.execute_sql(code)
    ans = output
    print(ans)

    gold = 'PHYS5.0FM4revA0\nRTL4.0FM4revA0\nRTL5.0FM4revA0'

    print("==========================================")
    if ans == gold:
        print("Test passed") 
        return 0
    else:
        print("Test failed")
        print(f"Expected: {gold}")
        print(f"Got: {ans}")
        return 1

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

