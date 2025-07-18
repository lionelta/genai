#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import logging
import os
import sys
import base64
import tempfile
import argparse
import subprocess
import json
from urllib.parse import urlencode
from pprint import pprint
rootdir = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main'
sys.path.insert(0, rootdir)
from lib.agents.base_agent import BaseAgent
import lib.genai_utils as gu


def main(args):

    LOGGER = logging.getLogger()
    level = logging.INFO
    if '--debug' in sys.argv:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)

    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    os.environ['AZURE_OPENAI_MODEL'] = 'gpt-4o'
    a = BaseAgent()
    a.kwargs['messages'] = [
        {
            'role': 'user', 
            'content': f'''Based on the following User Data, return a maximum of 3, minimum of 1 most important keywords you think is best to be used for Confluence CQL search.  
            DO NOT provide any additional statement or explanation. Just return the 5 words.   
            Example User Data:  
            I am trying to find out how to use the new feature in the latest version of our software.
            Example keywords:
            software feature latest 

            **User Data:**  
            {args.query} '''
        }
    ]
    res = a.run()
    print(res.message.content)
    keywords = res.message.content

    baseurl = 'https://altera-corp.atlassian.net/wiki'
    spaces_string = ','.join(args.spaces)
    query_string = ' '.join(args.query.split())
    endpoint = f'/rest/api/content/search'
    params = {
        "limit": args.limit,
        "cql": f'type=page and space in ({spaces_string}) and text ~ "{keywords}"'
    }
    fullurl = f'{baseurl}{endpoint}?{urlencode(params)}'
    LOGGER.debug(f'Searching wiki at {fullurl}')

    username = 'yoke.liang.lionel.tan@altera.com'
    token = open(os.path.join(rootdir, '.wiki_api_token'), 'r').read().strip()
    credentials = f'{username}:{token}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode("ascii")
    cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{fullurl}' """
    LOGGER.debug(f'get_confluence_decendants_of_page cmd: {cmd}')
    output = subprocess.getoutput(cmd)
    LOGGER.debug(f'get_confluence_decendants_of_page output: {output}')
    jsondata = json.loads(output)
    LOGGER.debug(f'get_confluence_decendants_of_page jsondata count: {len(jsondata["results"])}')
    print('------------------------------------------------')
    for result in jsondata['results']:
        url = f'{baseurl}{result["_links"]["webui"]}'
        print(url)
    print('------------------------------------------------')

    ### Get chunk data
    prompt = '**Context Chunks:**  \n\n'
    i = 1
    for result in jsondata['results']:
        pageid = result['id']
        endpoint = f'/api/v2/pages/{pageid}?body-format=storage'
        fullurl = f'{baseurl}{endpoint}'
        LOGGER.debug(f'Get page content at {fullurl}')
        cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{fullurl}' """
        LOGGER.debug(f'get_confluence_page_content cmd: {cmd}')
        output = subprocess.getoutput(cmd)
        LOGGER.debug(f'get_confluence_page_content output: {output}')
        jsondata = json.loads(output)
        content = jsondata['body']['storage']['value']
        
        prompt += f"""  
[Chunk {i}]  
Source: {baseurl}{result["_links"]["webui"]}  
Content: {content}   

"""
        i += 1

    prompt += f"""
**User Query:** {args.query}  
"""

    b = BaseAgent()
    b.kwargs['messages'] = [
        {
            'role': 'system',
            'content': systemprompt()
        },
        {
            'role': 'user',
            'content': prompt
        }
    ]
    res = b.run()
    print('------------------------------------------------')
    print(res.message.content)




def systemprompt():
    return """ You are a helpful and informative assistant. You will be provided with several chunks of information retrieved from various web pages.  These chunks are related to a user's query and are intended to provide context for your response.  **You MUST ONLY use the information provided in these chunks to answer the user's question.** Do not use any other knowledge or information.
Each chunk will be presented in the following format:
Source: https://en.wikipedia.org/wiki/Web_page  
Content: [Text content of the chunk]

The user's query will be provided after all the context chunks.

**Instructions:**

1. **Answer based on provided context:**  Answer the user's question using only the information provided in the context chunks.
2. **Cite sources:** If you use any information from a specific chunk in your answer, cite the source URL only at the very end of the response. Cite each source URL per line. (if there are multiple similar sources, you can cite them only once)
3. **Handle missing information:** If the provided context does not contain the answer to the user's question, respond with: "I'm sorry, but the provided information does not contain the answer to your question."  Do not attempt to answer based on your general knowledge.
4. **Be concise and relevant:**  Keep your answers concise and directly related to the user's question. Avoid unnecessary information or speculation.
5. **Maintain factual accuracy:** Ensure your response is factually accurate based on the provided context. Do not add or infer information that is not explicitly stated in the chunks.

**Context Chunks:**

[Chunk 1 - Example]
Source: https://www.example.com/article1
Content: The capital of France is Paris.  The population of Paris is approximately 2.1 million.

[Chunk 2 - Example]
Source: https://www.example.com/article2
Content:  Paris is located in the Île-de-France region.  It is known for its museums and historical landmarks.

[Chunk 3 - Example]
Source: https://www.example.com/article3
Content:  The Eiffel Tower is a famous landmark in Paris. It was built in 1889.

[Chunk 4 - Example]
Source: https://www.example.com/article4
Content:  The Louvre Museum is another popular attraction in Paris. It houses many famous works of art.

[Chunk 5 - Example]
Source: https://www.example.com/article5
Content:  France is a country in Western Europe. Its official language is French.

**User Query:** What is the population of Paris and where is it located?

**Example Response (using the above example context):**

The population of Paris is approximately 2.1 million. It is located in the Île-de-France region.

Source Of Information:  
1. https://www.example.com/article1  
2. https://www.example.com/article2  
"""

    



if __name__ == '__main__':
    epilog = '''Example Usage:
ask_then_search_wiki_and_answer.py --query "how to prevent my gk release from getting deleted?"
'''

    argparser = argparse.ArgumentParser(description='Search wiki for error message', epilog=epilog)
    argparser.add_argument('--debug', action='store_true', help='Enable debug mode')
    argparser.add_argument('--spaces', nargs='*', default=['tdmainfra', 'psgcth2tfm', 'kmtfmlynx', 'aidegenerictfm'], help='List of spaces to search in')
    argparser.add_argument('--limit', default=5, type=int, help='Limit number of wiki pages returned')
    argparser.add_argument('--query', required=True, help='Text To Search')
    args = argparser.parse_args()
    main(args)

