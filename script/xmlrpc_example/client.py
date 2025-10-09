#!/usr/intel/pkgs/python3/3.11.1/bin/python3

import UsrIntel.R1
import sys
import os
import xmlrpc.client
import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

def main():
    cmd = sys.argv[1]
    s = xmlrpc.client.ServerProxy('http://asccc16364923.sc.altera.com:8111', allow_none=True)
    ret = s.getstatusoutput(cmd)
    print(ret)

if __name__ == '__main__':
    sys.exit(main())

