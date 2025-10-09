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
import json
import subprocess
from pprint import pprint
import re

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

DMXLIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/lib/python'
CMXLIB = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/dmx/main_gdpxl_py23_cth/cmx/lib/python'
sys.path.insert(0, DMXLIB)
sys.path.insert(0, CMXLIB)

LOGGER = logging.getLogger()

def main():

    pageid = sys.argv[1]

    ### This cmd download html content of a confluence page
    # body-format = storage, atlas_doc_format, view, export_view, anonymous_export_view, styled_view, editor
    # GOOD: view, styled_view
    # BAD: storage
    fmt = 'view'
    cmd = f"""curl -s -H 'Authorization: Basic eW9rZS5saWFuZy5saW9uZWwudGFuQGFsdGVyYS5jb206QVRBVFQzeEZmR0YwTzhzUDdNTzRlYzdoMmZQSm5YT0Z3cFpOT3pHOU1RYVJWTGl3UzdZMEhWWWNPVnBsQnQ2czNpOFFYeFMzaVEwRnFEUjJuU3ZjcHQxZXlMSHVKanBFcWJQdEQ0MUZTYVh4MlZGZXVVcW9wbl9fS0RwZG5QOXp2cDJWbWJnUXRGdXZFaHZEdWJVdEZTY2xlb21DV18wNWZUVkhoVVhiQVhYRzJDZWVOc0lYZm5vPUY0MTQ3REFC' -H 'Content-Type: application/json' 'https://altera-corp.atlassian.net/wiki/api/v2/pages/{pageid}?body-format={fmt}' """
    output = subprocess.getoutput(cmd)  
    data = json.loads(output)

    # write confluence content to a html file
    with(open('page.html', 'w')) as f:
        f.write(data['body'][fmt]['value'])

    #============================================================================

    # convert html to markdown
    cmd = f"""/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/markitdown page.html > page.md"""
    os.system(cmd)
    #============================================================================

    # Convert page.md image url from
    #    ![](https://altera-corp.atlassian.net/wiki/download/attachments/46334408/image-2024-10-9_23-50-19.png?version=1&modificationDate=1728463819340&cacheVersion=1&api=v2)
    # to ...
    #    ![](<imgsrc="images/image-2024-10-9_23-50-19.png">)
    with open("page.md") as f:
        content = re.sub(r'\!\[\]\(https://altera-corp.atlassian.net/wiki/download/attachments/[0-9]*/(.*)\?.*\)', r'![](<imgsrc="images/\1">)', f.read())
    with open("page.md2", "w") as f:
        f.write(content)

    #============================================================================

    ### This cmd list all attachments a confluence page
    cmd = f"""curl -s -H 'Authorization: Basic eW9rZS5saWFuZy5saW9uZWwudGFuQGFsdGVyYS5jb206QVRBVFQzeEZmR0YwTzhzUDdNTzRlYzdoMmZQSm5YT0Z3cFpOT3pHOU1RYVJWTGl3UzdZMEhWWWNPVnBsQnQ2czNpOFFYeFMzaVEwRnFEUjJuU3ZjcHQxZXlMSHVKanBFcWJQdEQ0MUZTYVh4MlZGZXVVcW9wbl9fS0RwZG5QOXp2cDJWbWJnUXRGdXZFaHZEdWJVdEZTY2xlb21DV18wNWZUVkhoVVhiQVhYRzJDZWVOc0lYZm5vPUY0MTQ3REFC' -H 'Content-Type: application/json' 'https://altera-corp.atlassian.net/wiki/api/v2/pages/{pageid}/attachments' """
    output = subprocess.getoutput(cmd)
    data = json.loads(output)
    base_url = data['_links']['base']
    
    img_urls = []
    for attachment in data['results']:
        if 'image' in attachment['mediaType']:
            img_urls.append(base_url + attachment['downloadLink'])
    pprint(img_urls)
    #============================================================================

    # Download all images
    os.system('mkdir -p images')
    for img_url in img_urls:
        cmd = f"""cd images; curl -L -s -O -H 'Authorization: Basic eW9rZS5saWFuZy5saW9uZWwudGFuQGFsdGVyYS5jb206QVRBVFQzeEZmR0YwTzhzUDdNTzRlYzdoMmZQSm5YT0Z3cFpOT3pHOU1RYVJWTGl3UzdZMEhWWWNPVnBsQnQ2czNpOFFYeFMzaVEwRnFEUjJuU3ZjcHQxZXlMSHVKanBFcWJQdEQ0MUZTYVh4MlZGZXVVcW9wbl9fS0RwZG5QOXp2cDJWbWJnUXRGdXZFaHZEdWJVdEZTY2xlb21DV18wNWZUVkhoVVhiQVhYRzJDZWVOc0lYZm5vPUY0MTQ3REFC' '{img_url}' """
        os.system(cmd)
    #============================================================================

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

