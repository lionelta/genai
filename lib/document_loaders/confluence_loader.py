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
import base64
import subprocess
import json
import re
from pprint import pprint
import glob

import warnings
warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, rootdir)

import lib.genai_utils as gu
from langchain.schema import Document

class ConfluenceLoader():

    def __init__(self):
        self.logger = logging.getLogger()

        self.markitdown_exe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/markitdown'

        self.domain = 'altera-corp.atlassian.net'
        self.baseurl = f'https://{self.domain}/wiki'
        self.username = os.getenv("GENAI_CONFLUENCE_USERNAME", "yoke.liang.lionel.tan@altera.com")
        self.api_token = os.getenv("GENAI_CONFLUENCE_API_TOKEN", open(os.path.join(rootdir, '.wiki_api_token'), 'r').read().strip())
        self.spaces = []    # space name: provided by user
        self.pageids = []   # page ids: provided by user. Could be 123456 or +123456 or -654321
        self.final_pageids = [] # The final pageids, refer to docs in function `get_final_pageids` for detail
   
        self.savedir = ''   # REQUIRED: path to save all the files

    def get_basic_auth(self):
        credentials = f'{self.username}:{self.api_token}'
        encoded_credentials = base64.b64encode(credentials.encode()).decode("ascii")
        return encoded_credentials


    def get_final_pageids(self):
        ''' Extract all the pageids from self.spaces and self.pageids
        1. get all pageids under the given spaces in self.spaces
        2. get/expand all pageids from self.pageids whereby:
            - pageids that starts with +, which means we will extract all children pages including itself
            - pageids that starts with -, which means we will skip this page
            - pageids that are just numbers, which means we will extract only that page itself
        3. remove all pageids from self.pageids with '-' prefixed
        4. return the final pageids
        '''
        finals = []

        for space in self.spaces:
            finals.extend(self.get_pageids_from_space(space))

        for pageid in self.pageids:
            if pageid.startswith('+'):
                finals.append(pageid[1:])
                finals.extend(self.get_decendants_of_page(pageid[1:]))
            elif not pageid.startswith('+') and not pageid.startswith('-'):
                finals.append(pageid)

        finals = list(set(finals))

        for pageid in self.pageids:
            if pageid.startswith('-'):
                try:
                    finals.remove(pageid[1:])
                except:
                    pass

        self.final_pageids = finals
        return finals


    def get_space_id(self, name):
        endpoint = f'{self.baseurl}/api/v2/spaces?keys={name}'
        encoded_credentials = self.get_basic_auth()
        cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{endpoint}' """
        output = subprocess.getoutput(cmd)
        jsondata = json.loads(output)
        return jsondata['results'][0]['id']

    def get_pageids_from_space(self, space):
        spaceid = self.get_space_id(space)
        endpoint = f'{self.baseurl}/api/v2/spaces/{spaceid}/pages?limit=250'
        encoded_credentials = self.get_basic_auth()
        finals = []
        while endpoint:
            cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{endpoint}' """
            output = subprocess.getoutput(cmd)
            jsondata = json.loads(output)
            for page in jsondata['results']:
                finals.append(page['id'])
            endpoint = jsondata['_links'].get("next")
            if endpoint:
                endpoint = f'https://{self.domain}{endpoint}'
            else:
                endpoint = ''
        return finals


    def get_decendants_of_page(self, pageid):
        endpoint = f'{self.baseurl}/api/v2/pages/{pageid}/descendants?limit=250&depth=5'
        encoded_credentials = self.get_basic_auth()
        finals = []
        while endpoint:
            cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{endpoint}' """
            output = subprocess.getoutput(cmd)
            jsondata = json.loads(output)
            try:
                for page in jsondata['results']:
                    finals.append(page['id'])
                endpoint = jsondata['_links'].get("next")
                if endpoint:
                    endpoint = f'https://{self.domain}{endpoint}'
                else:
                    endpoint = ''
            except Exception as e:
                self.logger.warning(f"Failed getting descendants for {pageid}: {e}")
                endpoint = ''
        return finals

    def load(self):
        if not self.savedir:
            raise Exception("self.savedir not defined!")
        pageids = self.get_final_pageids()
        for pageid in pageids:
            try:
                self.save_page_content_as_html(pageid)
                self.convert_html_to_markdown(pageid)
                self.convert_markdown_image_source(pageid)
                self.save_page_images(pageid)
            except Exception as e:
                self.logger.warning(f"Failed getting content for {pageid}: {e}")

        # Only get the Documents if *.md2 file exists, and is not zero
        md2_files = glob.glob(os.path.join(self.outdir(), '*.md2'))

        documents = []
        for md2file in md2_files:
            with open(md2file) as f:
                content = f.read()
            
            metafile = md2file[:-3]+'meta'   # 123.md2 --> 123.meta
            with open(metafile) as f:
                metadata = json.load(f)
            documents.append(Document(page_content=content, metadata=metadata))
       
        # chmod everything under self.savedir to 775
        try:
            os.system(f'chmod -R 775 {self.savedir}')
        except:
            pass
        return documents

    def save_page_images(self, pageid):
        ### This cmd list all attachments a confluence page
        self.logger.info(f"Saving images for {pageid}")
        endpoint = f'{self.baseurl}/api/v2/pages/{pageid}/attachments?limit=250'
        encoded_credentials = self.get_basic_auth()
        cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{endpoint}' """
        output = subprocess.getoutput(cmd)  
        data = json.loads(output)
        
        output = subprocess.getoutput(cmd)
        data = json.loads(output)
        base_url = data['_links']['base']
        
        img_urls = []
        for attachment in data['results']:
            if 'image' in attachment['mediaType']:
                img_urls.append(base_url + attachment['downloadLink'])

        # Download all images
        os.system(f'mkdir -p {self.imgdir()}')
        for img_url in img_urls:
            cmd = f"""cd {self.imgdir()}; curl -L -s -O -H 'Authorization: Basic {encoded_credentials}' '{img_url}' """
            os.system(cmd)


    def convert_markdown_image_source(self, pageid):
        # Convert page.md image url from
        #    ![](https://altera-corp.atlassian.net/wiki/download/attachments/46334408/image-2024-10-9_23-50-19.png?version=1&modificationDate=1728463819340&cacheVersion=1&api=v2)
        # to ...
        #    ![](<imgsrc="images/image-2024-10-9_23-50-19.png">)
        self.logger.info(f"Converting md to md2 for {pageid}")
        with open(self.mdfile(pageid)) as f:
            #content = re.sub(r'\!\[.*\]\(https://altera-corp.atlassian.net/wiki/download/.*/[0-9]*/(.*)\?.*\)', r'![](<imgsrc="images/\1">)', f.read())
            content = re.sub(r'\!\[.*\]\(https://altera-corp.atlassian.net/wiki/download/.*/[0-9]*/(.*)\?.*\)', f'![](<imgsrc="{self.imgdir()}/\\1">)', f.read())
        with open(self.md2file(pageid), "w") as f:
            f.write(content)


    def convert_html_to_markdown(self, pageid):
        self.logger.info(f"Converting html to md for {pageid}")
        cmd = f"""{self.markitdown_exe} {self.htmlfile(pageid)} > {self.mdfile(pageid)}"""
        os.system(cmd)

    def save_page_content_as_html(self, pageid):
        self.logger.info(f"Saving html for {pageid} ...")
        fmt = 'view'
        endpoint = f'{self.baseurl}/api/v2/pages/{pageid}?body-format={fmt}'
        encoded_credentials = self.get_basic_auth()
        cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{endpoint}' """
        output = subprocess.getoutput(cmd)  
        data = json.loads(output)

        # write confluence content to a html file
        os.system(f"mkdir -p {self.outdir()}")
        with open(self.htmlfile(pageid), 'w') as f:
            f.write(data['body'][fmt]['value'])
        data = {
            'title': data['title'],
            'source': f"{self.baseurl}{data['_links']['webui']}"
        }
        with open(self.metafile(pageid), 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def outdir(self):
        return os.path.join(self.savedir, 'artifacts')

    def htmlfile(self, pageid):
        return os.path.join(self.outdir(), pageid+'.html')

    def metafile(self, pageid):
        return os.path.join(self.outdir(), pageid+'.meta')

    def mdfile(self, pageid):
        return os.path.join(self.outdir(), pageid+'.md')

    def md2file(self, pageid):
        return os.path.join(self.outdir(), pageid+'.md2')

    def imgdir(self):
        return os.path.realpath(os.path.join(self.outdir(), 'images'))

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

