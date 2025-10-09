#!/usr/intel/pkgs/python3/3.11.1/bin/python3

import UsrIntel.R1
import sys
import os
import subprocess
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ForkingMixIn
import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

class ForkingXMLRPCServer(ForkingMixIn, SimpleXMLRPCServer):
    max_children = 2  # Limit the number of concurrent child processes

def main():
    with ForkingXMLRPCServer(('0.0.0.0', 8111), allow_none=True) as server:
        server.register_function(getstatusoutput, 'getstatusoutput')
        print(f"Listening on port 8111 (max {server.max_children} processes) ...")
        server.serve_forever()

def getstatusoutput(cmdline):
    print(f"Running cmd: {cmdline}")
    return subprocess.getstatusoutput(cmdline)



if __name__ == '__main__':
    sys.exit(main())

