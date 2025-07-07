#!/usr/bin/env python

import subprocess 
from pprint import pprint
import sys
import os
import logging

rootdir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu


LOGGER = logging.getLogger(__name__)

print_user_guide_dict = {
    'type': 'function',
    'function': {
        'name': 'print_user_guide',
        'description': 'Print the user guide for this tool file',
        'parameters': {},
    }
}
def print_user_guide():
    txt = '''  

## Print Out This User Guide
    > myhelper -q 'user guide'
    > myhelper -q 'what can you do'

## Examples: Automation Helper
**To avoid confusion, use the keyword "help me automate:" in your query.**
    > myhelper -q 'help me automate: show me all the python files from current folder, one per line.'
    > myhelper -q 'help me automate: print out all the lines which matches the word "myhelper.py" in file ./unittests/manual_test_myhelper'
    > myhelper -q 'help me automate: replace all the word "myhelper" to "yourfriend" in file ./unittests/manual_test_myhelp, and save it to /tmp/a.b.c'
    > myhelper -q 'help me automate: rename all the files in current folder from <filename> to lionel_<filename>.txt'

## Examples: Explain Code
**To avoid confusion, use the keyword "explain these code:" in your query.**
    > myhelper -q 'explain these code in high level: ./bin/ask.py ./lib/agents/base_agent.py'
    > myhelper -q 'explain these code in low level:  /p/cth/cad/dmx/current/bin/*.py'
    > myhelper -q 'explain this code in mid level: a.py'

## Exmplaes: Generic Query
**To avoid confusion, use the keyword "generic query:" in your query.**
    > myhelper -q 'generic query: what is the capital of Malaysia'
    > myhelper -q 'generic query: explain what is python list'

## Examples: RAG Query
**To avoid confusion, use the keyword "faissdbs:" in your query.**
    > myhelper -q 'faissdbs: /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/psgcth2tfm/default /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/tdmainfra/default     QUERY: How to set a flow to non-gating?'
    > myhelper -q 'faissdbs: /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/psgcth2tfm/default /nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/tdmainfra/default     QUERY: How to create a new master git repo'

## Examples: Convert cmd output to json
**To avoid confusion, use the keyword "cmd2json:" in your query.**
    > myhelper -q 'cmd2json: Help convert the output of this command to json: ypcat passwd | grep lionelta. Use the following jsonformat: {<username>: {"userid":<userid>, "wwid":<alternate_id>}}}'
    > myhelper -q 'cmd2json: Help convert the output of this command to json: ls -al *.py'
    '''
    gu.print_markdown(txt, cursor_moveback=False)

#############################################################################
cmd2json_dict = {
    'type': 'function',
    'function': {
        'name': 'cmd2json',
        'description': 'Execute the given command and convert the output to json format.',
        'parameters': {
            'type': 'object',
            'properties': {
                'cmd': {
                    'type': 'string',
                    'description': 'the given cmd to be executed',
                    'required': True
                },
                'jsonformat': {
                    'type': 'string',
                    'description': 'the json format',
                    'required': False,
                    'default': ''
                }
            }
        }
    }
}
def cmd2json(cmd='', jsonformat=''):
    exe = os.path.join(rootdir, 'bin', 'cmd2json.py')
    cmd = '{} -c {}'.format(exe, gu.quotify(cmd))
    if jsonformat:
        cmd += ' -j {}'.format(gu.quotify(jsonformat))
    LOGGER.debug(f'Tool Ran: {cmd}')
    os.system(cmd)



#############################################################################
automater_dict = {
    'type': 'function',
    'function': {
        'name': 'automater',
        'description': 'Automate a task using the automater, only if the user asks for help to automate a task.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The FULL original user query, without any modifications',
                    'required': True,
                }
            }
        }
    }
}
def automater(query=''):
    exe = os.path.join(rootdir, 'bin', 'automater.py')
    cmd = '{} -q {}'.format(exe, gu.quotify(query))
    LOGGER.debug(f'Tool Ran: {cmd}')
    os.system(cmd)


#############################################################################
explain_code_dict = {
    'type': 'function',
    'function': {
        'name': 'explain_code',
        'description': 'explain the code of a given list of files, based on the given level.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filelist': {
                    'type': 'list',
                    'description': 'The list of files to be explained',
                    'required': True,
                },
                'level': {
                    'type': 'string',
                    'description': 'The level of detail for the explanation, whereby high is the least detailed, mid is the medium detailed, and low is the most detailed.',
                    'choices': ['high', 'mid', 'low'],
                    'default': 'high',
                    'required': False,
                }
            }
        }
    }
}
def explain_code(filelist='', level='high'):
    exe = os.path.join(rootdir, 'bin', 'explain_code.py')
    cmd = '{} -f {} -e {}'.format(exe, ' '.join(filelist), level)
    LOGGER.debug(f'Tool Ran: {cmd}')
    os.system(cmd)
    
#############################################################################
generic_query_dict = {
    'type': 'function',
    'function': {
        'name': 'generic_query',
        'description': 'Generic query to the LLM, if no other function is found',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The FULL original user query, without any modifications',
                    'required': True,
                }
            },
        },
    }
}
def generic_query(query=''):
    exe = os.path.join(rootdir, 'bin', 'ask.py')
    cmd = '{} -q {}'.format(exe, gu.quotify(query))
    LOGGER.debug(f'Tool Ran: {cmd}')
    os.system(cmd)
    

#############################################################################
rag_query_dict = {
    'type': 'function',
    'function': {
        'name': 'rag_query',
        'description': 'Do a RAG query to faiss database when a/some faiss database is provided.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The original user query, without the provided faiss database',
                    'required': True,
                },
                'faissdbs': {
                    'type': 'list',
                    'description': 'The list of faiss databases to be used',
                    'required': True,
                }
            },
        },
    }
}
def rag_query(query='', faissdbs=None):
    exe = os.path.join(rootdir, 'bin', 'ask.py')
    cmd = '{} -l {} -q {}'.format(exe, ' '.join(faissdbs), gu.quotify(query))
    LOGGER.debug(f'Tool Ran: {cmd}')
    os.system(cmd)
    


#all_tools = [print_user_guide_dict]
### Automatically get all the global variables which matches *_dict into a list
all_tools = [v for k, v in globals().items() if isinstance(v, dict) and k.endswith('_dict')]

def print_all_tools():
    print("=================================================")
    for tool in all_tools:
        print(f"Tool name: {tool['function']['name']}")
        print(f"Tool description: {tool['function']['description']}")
        print(f"Tool parameters: {tool['function']['parameters']}")
        print("=================================================")
