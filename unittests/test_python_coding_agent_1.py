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
import lib.agents.python_coding_agent

LOGGER = logging.getLogger()

def main():
    LOGGER.info('Starting the program')
    a = lib.agents.python_coding_agent.PythonCodingAgent()
    infile = os.path.join(os.path.dirname(__file__), 'test_python_coding_agent_1.txt')
    query = f'''help me extract out all the lines which matches the pattern "error"(case insensitive) from the file {infile}     

    **Each line of error looks like this:** [00:54:15 2025-04-14] [ERROR] Exception raised, initialising termination...
    **Expected error output looks like this:** Exception raised, initialising termination...  

    Report all gathered errors in a json list format.'''
    
    a.kwargs['messages'] = [{'role': 'user', 'content': query}]
    res = a.run()
    code = res.message['content']
    print("==========================================")
    print(code)
    print("==========================================")
    output = a.execute_code(code)
    ans = json.loads(output)
    print(ans)


    gold = ['Exception raised, initialising termination...',
 'Rtl filelist is missing for hip km_eth_l2p_macsec_rx_top',
 'Rtl filelist is missing for hip km_eth_l2p_macsec_rx_top']

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

