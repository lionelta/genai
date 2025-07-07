#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import os
import sys
import subprocess
import logging
import json

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent
from lib.agents.python_coding_agent import PythonCodingAgent

LOGGER = logging.getLogger()

#############################################################################
readfile_dict = {
    'type': 'function',
    'function': {
        'name': 'readfile',
        'description': 'read a single file and return its content',
        'parameters': {
            'type': 'object',
            'properties': {
                'filepath': {
                    'type': 'string',
                    'description': '',
                    'required': True,
                },
            },
        },
    }
}
def readfile(filepath):
    LOGGER.debug(f"Reading file: {filepath}")
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        LOGGER.debug("File content read successfully.")
        return content
    except Exception as e:
        LOGGER.debug(f"Error reading file {filepath}: {e}")
        return None
#############################################################################
read_multiple_files_dict = {
    'type': 'function',
    'function': {
        'name': 'read_multiple_files',
        'description': 'read multiple files and return their content as a list',
        'parameters': {
            'type': 'object',
            'properties': {
                'filelist': {
                    'type': 'list',
                    'description': 'List of file paths to read',
                    'required': True,
                },
            },
        },
    }
}
def read_multiple_files(filelist):
    LOGGER.debug(f"Reading multiple files: {filelist}")
    if isinstance(filelist, str):
        newlist = []
        for f in filelist.split('\n'):
            new = f.strip()
            if new:
                newlist.append(new)
        filelist = newlist

    contents = []
    for filepath in filelist:
        try:
            with open(filepath, 'r') as file:
                content = file.read()
            contents.append(content)
            LOGGER.debug(f"File {filepath} read successfully.")
        except Exception as e:
            LOGGER.debug(f"Error reading file {filepath}: {e}")
            contents.append(None)  # Append None if an error occurs
    return json.dumps(contents, indent=2)
#############################################################################
writefile_dict = {
    'type': 'function',
    'function': {
        'name': 'writefile',
        'description': 'write content to a file',
        'parameters': {
            'type': 'object',
            'properties': {
                'filepath': {
                    'type': 'string',
                    'description': 'File path to write to',
                    'required': True,
                },
                'content': {
                    'type': 'string',
                    'description': 'Content to write to the file',
                    'required': True,
                },
            },
        },
    }
}
def writefile(filepath, content):
    LOGGER.debug(f"Writing to file: {filepath}")
    try:
        with open(filepath, 'w') as file:
            file.write(content)
        LOGGER.debug("File written successfully.")
        return True
    except Exception as e:
        LOGGER.debug(f"Error writing to file {filepath}: {e}")
        return False
#############################################################################
get_temp_file_dict = {
    'type': 'function',
    'function': {
        'name': 'get_temp_file',
        'description': 'Get a temporary file path',
        'parameters': {
            'type': 'object',
            'properties': {},
        
            },
    }
}
def get_temp_file():
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    LOGGER.debug(f"Temporary file created: {temp_file.name}")
    return temp_file.name
#############################################################################
generate_python_code_dict = {
    'type': 'function',
    'function': {
        'name': 'generate_python_code',
        'description': 'Generate Python code to help automate tasks based on a prompt, writing the code into a temporary file. Return the fullpath to the generated code file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'prompt': {
                    'type': 'string',
                    'description': 'The prompt to generate Python code from',
                    'required': True,
                },
            },
        },
    }
}
def generate_python_code(prompt):
    LOGGER.debug("Generating Python code with prompt: {prompt}")
    agent = PythonCodingAgent()
    agent.kwargs['messages'] = [{'role': 'user', 'content': prompt}]
    agent.kwargs['stream'] = False
    res = agent.run()
    code = res.message.content
    cleancode = agent.remove_markdown(code)
    LOGGER.debug("Generated Python code successfully.")
    #return cleanccode
    return f"Python code generated and saved at {agent.codefile}"  # Return the path to the generated code file
#############################################################################
execute_python_code_dict = {
    'type': 'function',
    'function': {
        'name': 'execute_python_code',
        'description': 'Execute Python code and return the result',
        'parameters': {
            'type': 'object',
            'properties': {
                'filepath': {
                    'type': 'string',
                    'description': 'The fullpath to the python script to be executed',
                    'required': True,
                },
            },
        },
    }
}
def execute_python_code(filepath):
    LOGGER.debug("Executing Python code from file: {filepath}")
    cmd = f'python {filepath}'
    output = subprocess.getoutput(cmd)
    return output
    
#############################################################################
execute_system_command_dict = {
    'type': 'function',
    'function': {
        'name': 'execute_system_command',
        'description': 'Execute a system command and return the output',
        'parameters': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The system command to execute',
                    'required': True,
                },
            },
        },
    }
}
def execute_system_command(command):
    LOGGER.debug("Executing system command: {command}")
    try:
        output = subprocess.getoutput(command)
        LOGGER.debug("Command executed successfully.")
        return output
    except Exception as e:
        LOGGER.debug(f"Error executing command {command}: {e}")
        return None
#############################################################################
llm_dict = {
    'type': 'function',
    'function': {
        'name': 'llm',
        'description': 'As an Q&A llm agent, help answer the query/prompt.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The query to send to the LLM',
                    'required': True,
                },
            },
        },
    }
}
def llm(query):
    """Dispatch the query to a chatbot agent."""
    ba = BaseAgent()
    ba.kwargs['messages'] = [{'role': 'user', 'content': query}]
    ba.kwargs['stream'] = False
    res = ba.run()
    return res.message.content

#############################################################################
#############################################################################
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
