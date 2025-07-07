#!/usr/bin/env python

import subprocess 
from pprint import pprint
import sys
import os
import logging
import tempfile

rootdir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
import lib.agents.base_agent


LOGGER = logging.getLogger(__name__)



#############################################################################
read_file_dict = {
    'type': 'function',
    'function': {
        'name': 'read_file',
        'description': 'Agent that reads a file and returns its content',
        'parameters': {
            'type': 'object',
            'properties': {
                'filepath': {
                    'type': 'string',
                    'description': 'The filepath of the file to be read',
                    'required': True,
                }
            }
        }
    }
}
def read_file(filepath=''):
    return open(filepath, 'r').read()
#############################################################################
write_file_dict = {
    'type': 'function',
    'function': {
        'name': 'write_file',
        'description': 'Agent that writes the given content to a file, and returns the filepath',
        'parameters': {
            'type': 'object',
            'properties': {
                'content': {
                    'type': 'string',
                    'description': 'The content to be written to the file',
                    'required': True,
                }
            }
        }
    }
}
def write_file(content=''):
    filepath = tempfile.mkstemp(suffix='.py')[1]
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath
#############################################################################
python_coder_dict = {
    'type': 'function',
    'function': {
        'name': 'python_coder',
        'description': 'Agent that generates Python code based on the given task',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The task to be performed by the Python code',
                    'required': True,
                }
            },
        },
    }
}
def python_coder(query=''):
    pass
#############################################################################
python_runner_dict = {
    'type': 'function',
    'function': {
        'name': 'python_runner',
        'description': 'Agent that runs a given Python code, and returns the output',
        'parameters': {
            'type': 'object',
            'properties': {
                'filepath': {
                    'type': 'string',
                    'description': 'The filepath of the Python file to be executed',
                    'required': True,
                }
            },
        },
    }
}
def python_runner(filepath=''):
    pass
#############################################################################
llm_query_dict = {
    'type': 'function',
    'function': {
        'name': 'llm_query',
        'description': 'Agent that queries a language model with the given prompt',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The prompt to be sent to the language model',
                    'required': True,
                }
            },
        },
    }
}
def llm_query(query=''):
    pass

#############################################################################
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
