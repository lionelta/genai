#!/usr/intel/pkgs/python3/3.11.1/bin/python3

import base64
import sys

username = sys.argv[1]
token = sys.argv[2]
credential = f"{username}:{token}"
encoded_credentials = base64.b64encode(credential.encode()).decode("ascii")

print(encoded_credentials)

