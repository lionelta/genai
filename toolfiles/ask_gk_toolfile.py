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
# get_preserved_models
#
# This tool executes the following command to retrieve the list of preserved
# models (both dropbox and syncpoint) in JSON format, then normalizes and
# returns a unified JSON string that an LLM can easily consume:
#   /p/cth/cad/dmx/km6fe/cmx/bin/adm preserve \
#       --report --include-syncpoint --include-dropbox --json
#
# Returned structure (as stringified JSON) example:
# {
#   "summary": {"dropbox_models": 123, "syncpoint_models": 45, "unified_models": 130},
#   "models": [
#       {"name": "foo-a0-25ww10a", "domain": "DV", "milestone": "0.5a", "syncpoint_tag": "dropbox__DV__0.5a", "sources": ["dropbox","syncpoint"]},
#       {"name": "bar-a0-25ww11b", "domain": "Logical_FC_LUDO", "milestone": "0.5a", "sources": ["dropbox"]}
#   ]
# }
#
# Optional filters allow narrowing the results.
#############################################################################
get_preserved_models_dict = {
    'type': 'function',
    'function': {
        'name': 'get_preserved_models',
        'description': 'Return a unified list of preserved models (dropbox + syncpoint) with optional filters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_domain': {
                    'type': 'string',
                    'description': 'Only include models whose domain matches (substring, case-insensitive).',
                },
                'filter_milestone': {
                    'type': 'string',
                    'description': 'Only include models whose milestone matches (substring, case-insensitive).',
                },
                'filter_name': {
                    'type': 'string',
                    'description': 'Only include models whose name contains this substring (case-insensitive).',
                },
                'source': {
                    'type': 'string',
                    'description': 'Limit to a specific source: dropbox | syncpoint | both (default both).',
                },
                'limit': {
                    'type': 'string',
                    'description': 'Maximum number of models to return (after filtering). Provide a numeric string (e.g. "25").',
                }
            },
        },
    }
}
def get_preserved_models(filter_domain: str = None,
                         filter_milestone: str = None,
                         filter_name: str = None,
                         source: str = 'both',
                         limit: str = None):
    """Fetch and return preserved models with optional filtering.

    Parameters mirror the tool schema. Returns a JSON string (not a Python
    object) so that downstream LLMs can easily consume / display it.
    """
    cmd = [
        '/p/cth/cad/dmx/wplim_dev/cmx/bin/adm', 'preserve', '--report',
        '--include-syncpoint', '--include-dropbox', '--json'
    ]
    try:
        raw = subprocess.check_output(cmd, text=True)
    except Exception as e:
        return json.dumps({'error': f'Failed running preserve command: {e}'})

    try:
        data = json.loads(raw)
    except Exception as e:
        return json.dumps({'error': f'Failed parsing JSON output: {e}'})

    dropbox_models = data.get('dropbox', {}).get('models', {})  # name -> {domain, milestone}
    syncpoint_models = data.get('syncpoint', {}).get('models', {})  # name -> tag string
    # Waiver information (top-level)
    waiver_file = data.get('waiver_file')
    waivers_list = data.get('waivers', []) or []  # list of model names waived
    waivers_set = set(waivers_list)

    unified = {}
    # Incorporate dropbox first
    for name, meta in dropbox_models.items():
        unified[name] = {
            'name': name,
            'domain': meta.get('domain'),
            'milestone': meta.get('milestone'),
            'syncpoint_tag': None,
            'sources': ['dropbox'],  # waiver now modeled as an additional source label 'waiver'
        }
    # Merge syncpoint
    for name, tag in syncpoint_models.items():
        if not name:
            continue  # skip empty key if present
        entry = unified.get(name)
        if entry is None:
            entry = {
                'name': name,
                'domain': None,
                'milestone': None,
                'syncpoint_tag': None,
                'sources': ['syncpoint'],
            }
            unified[name] = entry
        if tag:
            entry['syncpoint_tag'] = tag
        if 'syncpoint' not in entry['sources']:
            entry['sources'].append('syncpoint')

    # Add waiver as a distinct source if applicable
    for wname in waivers_set:
        entry = unified.get(wname)
        if entry is None:
            # A waived model that isn't in dropbox or syncpoint lists
            unified[wname] = {
                'name': wname,
                'domain': None,
                'milestone': None,
                'syncpoint_tag': None,
                'sources': ['waiver'],
            }
        else:
            if 'waiver' not in entry['sources']:
                entry['sources'].append('waiver')

    # Apply filters
    def _match(val, pattern):
        if pattern is None:
            return True
        if val is None:
            return False
        return pattern.lower() in str(val).lower()

    src_filter = (source or 'both').lower()
    filtered = []
    for m in unified.values():
        if src_filter != 'both':
            if src_filter == 'dropbox' and 'dropbox' not in m['sources']:
                continue
            if src_filter == 'syncpoint' and 'syncpoint' not in m['sources']:
                continue
        if not _match(m.get('domain'), filter_domain):
            continue
        if not _match(m.get('milestone'), filter_milestone):
            continue
        if not _match(m.get('name'), filter_name):
            continue
        filtered.append(m)

    # Sort deterministically by name
    filtered.sort(key=lambda x: x['name'])

    if limit is not None:
        try:
            l = int(limit)
            if l >= 0:
                filtered = filtered[:l]
        except ValueError:
            pass

    returned_waived_models = sum(1 for m in filtered if 'waiver' in m.get('sources', []))

    result = {
        'summary': {
            'dropbox_models': len(dropbox_models),
            'syncpoint_models': len(syncpoint_models),
            'unified_models': len(unified),
            'returned_models': len(filtered),
            'total_waived_models': data.get('total_waived_models', len(waivers_set)),
            'returned_waived_models': returned_waived_models,
            'waiver_file': waiver_file,
            'filters': {
                'filter_domain': filter_domain,
                'filter_milestone': filter_milestone,
                'filter_name': filter_name,
                'source': src_filter,
                'limit': limit,
            }
        },
    'models': filtered,
    'waivers': waivers_list,  # echo original list for transparency; waiver treated as a source label
    }
    try:
        return json.dumps(result, indent=2)
    except Exception:
        # Fallback minimal serialization
        return json.dumps({'error': 'Serialization failure'})


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
git_compare_dict = {
    'type': 'function',
    'function': {
        'name': 'git_compare',
        'description': 'Compare two git directories and provide a summary of changes between them. Automatically extracts the model name from directory names and uses the IP_MODELS environment variable as the base path.',
        'parameters': {
            'type': 'object',
            'properties': {
                'dir1': {
                    'type': 'string',
                    'description': 'First directory name (e.g., bypass_pnr_reg-a0-25ww39e)',
                    'required': True,
                },
                'dir2': {
                    'type': 'string',
                    'description': 'Second directory name (e.g., bypass_pnr_reg-a0-25ww39f)',
                    'required': True,
                },
                'base_path': {
                    'type': 'string',
                    'description': 'Base path (default: IP_MODELS + "/release"; if IP_MODELS is not set the script falls back to /nfs/site/disks/psg.mod.000)',
                },
            },
        },
    }
}
def git_compare(dir1, dir2, base_path=None):
    """Compare two git directories using the git_compare.py script.

    This function calls the git_compare.py script located in the compare_model directory
    and returns the comparison results.

    Args:
        dir1: First directory name
        dir2: Second directory name
        base_path: Optional base path. If omitted, the script will use the
                   environment variable IP_MODELS with "/release" appended
                   (or the script's own fallback of '/nfs/site/disks/psg.mod.000' if IP_MODELS is unset).

    Returns:
        String containing the comparison results or error message
    """
    LOGGER.debug(f"Comparing git directories: {dir1} vs {dir2}")
    
    try:
        # Path to the git_compare.py script
        script_path = "/p/psg/da/infra/utils/bin/git_compare_models"
        
        # Build the command. Only pass --base-path when explicitly provided by caller.
        cmd = [script_path, dir1, dir2]
        if base_path:
            cmd.extend(['--base-path', base_path])
        
        # Execute the script
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            LOGGER.debug("Git comparison completed successfully.")
            return result.stdout
        else:
            error_msg = f"Git comparison failed with return code {result.returncode}:\n{result.stderr}"
            LOGGER.debug(error_msg)
            return error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "Git comparison timed out after 5 minutes"
        LOGGER.debug(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error running git comparison: {e}"
        LOGGER.debug(error_msg)
        return error_msg

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
