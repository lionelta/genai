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
get_tag_diff_dict = {
    'type': 'function',
    'function': {
        'name': 'get_tag_diff',
        'description': 'Get the the tag difference by providing two release model or ip model',
        'parameters': {
            'type': 'object',
            'properties': {
                'modelname1': {
                    'type': 'string',
                    'description': 'The release model name to get tag differences',
                    'required': True,
                },
                'modelname2': {
                    'type': 'string',
                    'description': 'The release model name to get tag differences',
                    'required': True,
                },
            },
        },
    }
}
def get_tag_diff(modelname1, modelname2):
    LOGGER.debug(f"Getting tag diff for release model: {modelname1} {modelname2}")
    reponame1, _ = modelname1.split('-a0-')
    reponame2, _ = modelname2.split('-a0-')
    if reponame1 != reponame2:
        LOGGER.debug(f"{modelname1} and {modelname2} is not under same IP")
        return None
    try:
        git_repo_path = os.path.realpath(os.path.join(os.getenv('GIT_REPOS', '/nfs/site/disks/psg.git.001'), 'git_repos', reponame1))
        cmd = f'cd {git_repo_path}; git diff {modelname1} {modelname2} '
        output = subprocess.getoutput(cmd)
        LOGGER.debug("Git diff retrieved successfully.")
        return output 
    except Exception as e:
        LOGGER.debug(f"Error getting git diff for release model {modelname1} and {modelname2}")
        return None

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
get_feeder_url_dict = {
    'type': 'function',
    'function': {
        'name': 'get_feeder_url',
        'description': 'Get the feeder URL for a release model',
        'parameters': {
            'type': 'object',
            'properties': {
                'modelname': {
                    'type': 'string',
                    'description': 'The release model name to get the feeder URL from',
                    'required': True,
                },
            },
        },
    }
}
def get_feeder_url(modelname):
    LOGGER.debug(f"Getting feeder URL for release model: {modelname}")
    reponame, _ = modelname.split('-a0-')
    try:
        logfile = os.path.join(os.getenv('IP_MODELS', '/nfs/site/disks/psg.mod.000'), 'release', reponame, modelname, 'GATEKEEPER', 'gk-utils.log')
        cmd = f'grep feeder {logfile} | grep URL'
        output = subprocess.getoutput(cmd)
        LOGGER.debug("Feeder URL retrieved successfully.")
        return output
    except Exception as e:
        LOGGER.debug(f"Error getting feeder URL for release model {modelname}: {e}")
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
        ... where <yy> is the year, <ww> is the week number, and <#> is running character. 
        Models without branchname are the main/master branch models, while those with branchname are the branch models.   
        - repo_name-a0-23ww11a (this is a main/master branch model)  
        - repo_name-a0-my_little_0.2-23ww11b (this is a branch model, where my_little_0.2 is the branch name)  

        Example:-  
            repo_name-a0-23w01b is later than repo_name-a0-23w01a (because b > a)  
            repo_name-a0-23w01b is later than repo_name-a0-22w01b (because year 23 > 22)  
            repo_name-a0-23w13b is later than repo_name-a0-23w01a (because week 13 > week 01)  
            repo_name-a0-24w10b is later than repo_name-a0-23w13c (because year 24 > 23)

        Note: <yy> has highest priority, followed by <ww>, and then <#>.  

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
