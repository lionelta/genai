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
get_baseline_tool_dict = {
    'type': 'function',
    'function': {
        'name': 'get_baseline_tool',
        'description': 'Get the baseline tool for a release model',
        'parameters': {
            'type': 'object',
            'properties': {
                'modelname': {
                    'type': 'string',
                    'description': 'The release model name to get the baseline tool from',
                    'required': True,
                },
            },
        },
    }
}
def get_baseline_tool(modelname):
    LOGGER.debug(f"Getting baseline tool for release model: {modelname}")
    reponame, _ = modelname.split('-a0-')
    try:
        baseline_tool_file = os.path.realpath(os.path.join(os.getenv('IP_MODELS', '/nfs/site/disks/psg.mod.000'), 'release', reponame, modelname, 'baseline_tools'))
        LOGGER.debug("Baseline tool retrieved successfully.")
        return baseline_tool_file
    except Exception as e:
        LOGGER.debug(f"Error getting baseline tool for release model {modelname}: {e}")
        return None
#############################################################################
get_job_result_dict = {
    'type': 'function',
    'function': {
        'name': 'get_job_result',
        'description': 'Get the job results for a release model',
        'parameters': {
            'type': 'object',
            'properties': {
                'modelname': {
                    'type': 'string',
                    'description': 'The release model name to get job results from',
                    'required': True,
                },
            },
        },
    }
}
def get_job_result(modelname):
    LOGGER.debug(f"Getting job results for release model: {modelname}")
    reponame, _ = modelname.split('-a0-')
    try:
        job_result_file = os.path.join(os.getenv('IP_MODELS', '/nfs/site/disks/psg.mod.000'), 'release', reponame, modelname, 'GATEKEEPER', 'gk_report.txt')
        with open(job_result_file, 'r') as file:
            job_result = file.read()
        LOGGER.debug("Job results retrieved successfully.")
        return job_result
    except Exception as e:
        LOGGER.debug(f"Error getting job results for release model {modelname}: {e}")
        return None
#############################################################################
list_all_models_dict = {
    'type': 'function',
    'function': {
        'name': 'list_all_models',
        'description': 'List all available models for a repo name',
        'parameters': {
            'type': 'object',
            'properties': {
                'repo_name': {
                    'type': 'string',
                    'description': 'The repository name to list models from',
                    'required': True,
                },
            },
        },
    }
}
def list_all_models(repo_name):
    LOGGER.debug(f"Listing all models for repo: {repo_name}")
    try:
        ret = os.listdir(os.path.join(os.getenv('IP_MODELS', '/nfs/site/disks/psg.mod.000'), 'release', repo_name))
        ### Remove all *-latest models
        ret = [model for model in ret if not model.endswith('-latest')]
        all_models = json.dumps(ret, indent=2)
        LOGGER.debug("Models listed successfully.")
        prompt = f"""
        The models naming convention is as follows:
        <repo_name>-a0[-branchname]-<timestamp>   
        ... whereby <timestamp> is in the format of <yy>ww<ww><#>   
        ... where <yy> is the year, ww is the week number, and <#> is running character where b is later than a).   
        Models without branchname are the main/master branch models, while those with branchname are the branch models.  

        Here is the list of models:  
        {all_models}  
        """
        return prompt   
    except Exception as e:
        LOGGER.debug(f"Error listing models for repo {repo_name}: {e}")
        return None
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
