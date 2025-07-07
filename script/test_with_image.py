#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import logging
import os
import sys
import base64
sys.path.insert(0, '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main')
from lib.agents.base_agent import BaseAgent

def main():
    base64_image = get_base64_image('./aidash.png')
    prompt = 'summarize what u see in this image, and tabulate out the design scores.'

    ### Openai format
    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    a = BaseAgent()
    a.kwargs['messages'] = [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url":{ "url": f"data:image/png;base64,{base64_image}"}},
        ]
         }]
    res = a.run()
    print(res)
    print("======================")
    print(res.message.content)

    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    
    ### Ollama format
    del os.environ['AZURE_OPENAI_API_KEY']
    a = BaseAgent()
    a.kwargs['model'] = 'llava'
    a.kwargs['messages'] = [
            {
                "role": "user", 
                "content": prompt,
                'images': [base64_image]
            }
         ]
    res = a.run()
    print(res)
    print("======================")
    print(res.message.content)

def get_base64_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.INFO)
    main()

