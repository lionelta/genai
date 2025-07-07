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
    infile = os.path.join(os.path.dirname(__file__), 'test_python_coding_agent_2.txt')
    query = f'''help me extract out a csv file data({infile}). For all the rows, get the data from column 3 and 5, and return me the result in a json format that looks like this {{"row 1 column 3": <row 1 column 3 data>, "row 1 column 5": <row 1 column 5 data>, "row 2 column 3": <row 2 column 3 data>, ...}}. '''

    a.kwargs['messages'] = [{'role': 'user', 'content': query}]
    res = a.run()
    code = res.message['content']
    print("==========================================")
    print(code)
    print("==========================================")
    output = a.execute_code(code)
    ans = json.loads(output)
    print(ans)

    gold = {'row 1 column 3': ' aaa', 'row 1 column 5': ' aaaaa', 'row 2 column 3': ' bbb', 'row 2 column 5': ' bbbbb', 'row 3 column 3': ' ccc', 'row 3 column 5': ' ccccc'}

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

