#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

import os
import sys
import subprocess
import logging
import json
import requests

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent
from lib.agents.python_coding_agent import PythonCodingAgent

LOGGER = logging.getLogger()

#############################################################################
# Helper Functions
#############################################################################
def _call_pdd_api(endpoint, operation_name):
    """Generic helper to call PDD (Physical Design Data) API endpoints.
    
    Args:
        endpoint: URL path relative to base (e.g., 'healthcheck', 'version')
        operation_name: Human-readable operation name for logging
        
    Returns:
        JSON string with the API response or error
    """
    LOGGER.debug(f"{operation_name}")
    try:
        url = f'https://ui-api.pdd.altera.com/{endpoint}'
        headers = {'accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=10, proxies={"http": "", "https": ""}, verify=False)
        response.raise_for_status()
        
        result = response.json()
        LOGGER.debug(f"{operation_name} succeeded.")
        return json.dumps(result)
    except requests.exceptions.Timeout:
        error_msg = f'Request timed out while {operation_name}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except requests.exceptions.ConnectionError as e:
        error_msg = f'Connection error while {operation_name}: {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except requests.exceptions.HTTPError as e:
        error_msg = f'HTTP error while {operation_name}: {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except Exception as e:
        error_msg = f'Failed to {operation_name}: {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})

def _clean_up_json(json_str, main_key, keys_to_remove):
    """Remove specified keys from each dictionary in a list.
    
    Args:
        json_str: json string with list of dictionaries
        keys_to_remove: List of keys to remove from each dictionary

    Returns:
        List of dictionaries with specified keys removed
    """
    data_json = json.loads(json_str)
    if 'error' in data_json:
        return json_str
    if main_key is not None and main_key not in data_json:
        LOGGER.debug(f"Main key '{main_key}' not found in data_json")
        return json_str
    if main_key is None:
        data_json2 = data_json
    else:
        data_json2 = data_json[main_key]
    if not isinstance(data_json2, list):
        LOGGER.debug("Invalid data_json format")
        return data_json

    cleaned_data = []
    for item in data_json2:
        if not isinstance(item, dict):
            LOGGER.debug("Invalid item format")
            continue
        cleaned_item = {k: v for k, v in item.items() if k not in keys_to_remove}
        # LOGGER.debug(f"Cleaned item: {cleaned_item}")
        cleaned_data.append(cleaned_item)
    return json.dumps(cleaned_data)
#############################################################################
# get_pdd_health
#
# This tool executes a REST API call to retrieve the health status of the PDD
# (Physical Design Data) system. It queries the healthcheck endpoint and returns
# the response in JSON format.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/healthcheck
# Expected Response:
# {
#   "status": "healthy"
# }
#
#############################################################################
get_pdd_health_dict = {
    'type': 'function',
    'function': {
        'name': 'get_pdd_health',
        'description': 'Check the health status of the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {},
        },
    }
}
def get_pdd_health():
    """Fetch and return PDD health status.
    
    Returns a JSON string containing the health status of the PDD system.
    """
    return _call_pdd_api('healthcheck', 'checking PDD health status')

#############################################################################
# get_pdd_version
#
# This tool executes a REST API call to retrieve the version information of the PDD
# (Physical Design Data) system. It queries the version endpoint and returns
# the response in JSON format.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/version
# Expected Response:
# {
#   "version": "2.3.251013-8c59ee"
# }
#
#############################################################################
get_pdd_version_dict = {
    'type': 'function',
    'function': {
        'name': 'get_pdd_version',
        'description': 'Get the version information of the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {},
        },
    }
}
def get_pdd_version():
    """Fetch and return PDD version information.
    
    Returns a JSON string containing the version of the PDD system.
    """
    return _call_pdd_api('version', 'getting PDD version')

#############################################################################
# get_user_list
#
# This tool executes a REST API call to retrieve the list of users in the PDD
# (Physical Design Data) system. Returns user details including id, uuid, email,
# active status, admin flags, and last login information.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/user/list
# Expected Response:
# {
#   "users": [
#       {
#           "id": "cfchua",
#           "uuid": "ec94673e-e319-412c-82a7-3ab687c6aabe",
#           "idsid": "cfchua",
#           "email": "cfchua@altera.com",
#           "is_active": true,
#           "is_superuser": false,
#           "is_admin": false,
#           "remark": "Auto-created from the metadata file",
#           "last_login": "2025-04-21T06:36:29.719082"
#       },
#       ...
#   ]
# }
#
#############################################################################
get_user_list_dict = {
    'type': 'function',
    'function': {
        'name': 'get_user_list',
        'description': 'Get the list of all users in the PDD (Physical Design Data) system with their details.',
        'parameters': {
            'type': 'object',
            'properties': {},
        },
    }
}
def get_user_list():
    """Fetch and return list of PDD users.
    
    Returns a JSON string containing all users and their details in the PDD system.
    """
    data = _call_pdd_api('v1/api/user/list', 'retrieving PDD user list')
    data = _clean_up_json(data, 'users', ['id', 'is_active', 'is_superuser', 'is_admin', 'remark'])
    return data

#############################################################################
# get_subsystem_list
#
# This tool executes a REST API call to retrieve the list of subsystems in the PDD
# (Physical Design Data) system. Returns subsystem details including id, name, uuid,
# and the user who created it.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/subsystem/list
# Expected Response:
# {
#   "subsystems": [
#       {
#           "name": "HSIO",
#           "uuid": "3b69bfba-d719-4a57-8e39-60ef418eb62a",
#       },
#       {
#           "name": "E400S",
#           "uuid": "e2149262-e15a-433a-a64e-521b983a31ee",
#       },
#       ...
#   ]
# }
#
#############################################################################
get_subsystem_list_dict = {
    'type': 'function',
    'function': {
        'name': 'get_subsystem_list',
        'description': 'Get the list of all subsystems in the PDD (Physical Design Data) system with their details.',
        'parameters': {
            'type': 'object',
            'properties': {},
        },
    }
}
def get_subsystem_list():
    """Fetch and return list of PDD subsystems.
    
    Returns a JSON string containing all subsystems and their details in the PDD system.
    """
    data = _call_pdd_api('v1/api/subsystem/list', 'retrieving PDD subsystem list')
    data = _clean_up_json(data, 'subsystems', ['id', 'created_by'])
    return data

#############################################################################
# get_subsystem_uuid
#
# This tool retrieves the UUID of a subsystem by its name from the PDD
# (Physical Design Data) system. It queries the subsystem list and filters
# by name to return the matching UUID.
#
# Takes subsystem_name as parameter and returns the UUID if found.
#
#############################################################################
get_subsystem_uuid_dict = {
    'type': 'function',
    'function': {
        'name': 'get_subsystem_uuid',
        'description': 'Get the UUID of a subsystem by its name in the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subsystem_name': {
                    'type': 'string',
                    'description': 'The name of the subsystem (e.g., HSIO, E400S)',
                    'required': True,
                },
            },
        },
    }
}
def get_subsystem_uuid(subsystem_name):
    """Fetch and return the UUID of a subsystem by name.
    
    Args:
        subsystem_name: The name of the subsystem
        
    Returns:
        A JSON string containing the UUID of the subsystem if found, or an error message.
    """
    try:
        json_str = get_subsystem_list()
        subsystem_data = json.loads(json_str)
        
        # Handle error response
        if 'error' in subsystem_data:
            return json_str
        
        for subsystem in subsystem_data:
            subsystem_name_from_data = subsystem.get('name', '')
            # Try exact match first (case-insensitive)
            if subsystem_name_from_data.lower() == subsystem_name.lower():
                uuid = subsystem.get('uuid')
                return uuid
            try:
                import re
                if re.search(subsystem_name, subsystem_name_from_data, re.IGNORECASE):
                    uuid = subsystem.get('uuid')
                    print(f"Found subsystem {subsystem_name} with UUID {uuid} (regex match)")
                    return uuid
            except re.error:
                pass
        # If not found
        error_msg = f'Subsystem "{subsystem_name}" not found in PDD system'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except Exception as e:
        error_msg = f'Failed to get subsystem UUID for "{subsystem_name}": {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    
#############################################################################
# get_block_subsystem
#
# This tool retrieves the UUID of a subsystem that the block belongs to by its name from the PDD
# (Physical Design Data) system. It queries the subsystem list and filters
# by name to return the matching UUID.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/subsystem/list/with_blocks
# Expected Response:
#   {"subsystem_name": "mktest", "subsystem_uuid": "2f62ee90-5038-44cb-88bb-3f2674a72964"}
#
# Takes block name as parameter and returns the UUID if found.
#
#############################################################################
get_block_subsystem_uuid_dict = {
    'type': 'function',
    'function': {
        'name': 'get_block_subsystem_name',
        'description': 'Get the name of the subsystem this block belongs to in the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'block_name': {
                    'type': 'string',
                    'description': 'The name of the block (e.g., ioss3ddr5mcsf)',
                    'required': True,
                },
            },
        },
    }
}
def get_block_subsystem_name(block_name):
    """Fetch and return the name of the subsystem this block belongs to.

    Args:
        block_name: The name of the block
        
    Returns:
        A string of the subsystem name.
    """
    try:
        # Get all subsystems
        subsystems_json = _call_pdd_api('v1/api/subsystem/list/with_blocks', 'retrieving PDD subsystem list')
        subsystems_data = json.loads(subsystems_json)
        # Handle error response
        if 'error' in subsystems_data:
            return subsystems_json
        
        # Search for matching subsystem by name (case-insensitive)
        subsystems_list = subsystems_data.get('subsystems', [])
        for subsystem in subsystems_list:
            subsystem_name = subsystem.get('name', '')
            uuid = subsystem.get('uuid')
            blocks_list = subsystem.get('blocks', [])
            for block in blocks_list:
                block_name_from_data = block.get('name', '')
                if block_name_from_data.lower() == block_name.lower():
                    return subsystem_name
    except Exception as e:
        error_msg = f'Failed to find subsystem UUID for block "{block_name}": {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    error_msg = f'Block "{block_name}" not found in PDD system'
    LOGGER.debug(error_msg)
    return json.dumps({'error': error_msg})

#############################################################################
# get_block_list_by_subsystem
#
# This tool executes a REST API call to retrieve the list of blocks for a specific
# subsystem in the PDD (Physical Design Data) system. Returns block details including
# id, name, uuid, custom_name, start_date, and the user who created it.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/block/list_by_subsystem/{subsystem_uuid}
# Expected Response:
# [
#       {
#           "name": "ioss3_ddr5_mc_sf",
#           "uuid": "69cf19ce-db31-4254-b097-b7c50237a6c0",
#       },
#       {
#           "name": "ioss3_lpddr_mc_sf",
#           "uuid": "874b297b-03e5-4e0d-9132-bce6498c0e6b",
#       },
#       ...
# ]
#
#############################################################################
get_block_list_by_subsystem_dict = {
    'type': 'function',
    'function': {
        'name': 'get_block_list_by_subsystem',
        'description': 'Get the list of all blocks for a specific subsystem in the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subsystem_uuid': {
                    'type': 'string',
                    'description': 'The UUID of the subsystem (can be obtained from get_subsystem_uuid or get_subsystem_list)',
                    'required': True,
                },
            },
        },
    }
}
def get_block_list_by_subsystem(subsystem_uuid):
    """Fetch and return list of blocks for a specific subsystem.
    
    Args:
        subsystem_uuid: The UUID of the subsystem
        
    Returns:
        A JSON string containing all blocks in the subsystem.
    """
    endpoint = f'v1/api/block/list_by_subsystem/{subsystem_uuid}'
    data = _call_pdd_api(endpoint, f'retrieving blocks for subsystem {subsystem_uuid}')
    data = _clean_up_json(data, 'blocks', ['id', 'custom_name', 'start_date', 'created_by'])
    return data

#############################################################################
# get_subsystem_experiment_tags
#
# This tool executes a REST API call to retrieve all experiment tags for a specific
# subsystem in the PDD (Physical Design Data) system.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/subsystem/{subsystem_uuid}/all_experiment_tags
# Expected Response:
# [
#     "0.5B"
# ]
#
#############################################################################
get_subsystem_experiment_tags_dict = {
    'type': 'function',
    'function': {
        'name': 'get_subsystem_experiment_tags',
        'description': 'Get all experiment tags for a specific subsystem in the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subsystem_uuid': {
                    'type': 'string',
                    'description': 'The UUID of the subsystem (can be obtained from get_subsystem_uuid or get_subsystem_list)',
                    'required': True,
                },
            },
        },
    }
}
def get_subsystem_experiment_tags(subsystem_uuid):
    """Fetch and return all experiment tags for a specific subsystem.
    
    Args:
        subsystem_uuid: The UUID of the subsystem
        
    Returns:
        A JSON string containing all experiment tags for the subsystem.
    """
    endpoint = f'v1/api/subsystem/{subsystem_uuid}/all_experiment_tags'
    return _call_pdd_api(endpoint, f'retrieving experiment tags for subsystem {subsystem_uuid}')

#############################################################################
# get_block_experiment_tags
#
# This tool executes a REST API call to retrieve experiment tags for a specific block
# within a subsystem in the PDD (Physical Design Data) system.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/subsystem/{subsystem_uuid}/block/{block_uuid}/experiment_tags
# Expected Response:
# [
#     "0.5B"
# ]
#
#############################################################################
get_block_experiment_tags_dict = {
    'type': 'function',
    'function': {
        'name': 'get_block_experiment_tags',
        'description': 'Get experiment tags for a specific block within a subsystem in the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subsystem_uuid': {
                    'type': 'string',
                    'description': 'The UUID of the subsystem (can be obtained from get_subsystem_uuid or get_subsystem_list)',
                    'required': True,
                },
                'block_uuid': {
                    'type': 'string',
                    'description': 'The UUID of the block (can be obtained from get_block_list_by_subsystem, need to extract from there)',
                    'required': True,
                },
            },
        },
    }
}
def get_block_experiment_tags(subsystem_uuid, block_uuid):
    """Fetch and return experiment tags for a specific block in a subsystem.
    
    Args:
        subsystem_uuid: The UUID of the subsystem
        block_uuid: The UUID of the block
        
    Returns:
        A JSON string containing all experiment tags for the block.
    """
    endpoint = f'v1/api/subsystem/{subsystem_uuid}/block/{block_uuid}/experiment_tags'
    return _call_pdd_api(endpoint, f'retrieving experiment tags for block {block_uuid} in subsystem {subsystem_uuid}')

#############################################################################
# get_unique_metric_names
#
# This tool executes a REST API call to retrieve unique metric names
# in the PDD (Physical Design Data) system.
#
# API Endpoint: GET https://ui-api.pdd.altera.com/v1/api/report/unique_metric_names
#
# Expected Response:
# [
#   "",
#   "C_rt_to_m80k_Setup WS",
#   "FUNC.SETUP.clk_m20_dsp_clk2.CNT",
#   "scanshift.SETUP.s_regscan_clk_ips_clk0regscan.TNS",
#  ...
# ]
#############################################################################
get_unique_metric_names_dict = {
    'type': 'function',
    'function': {
        'name': 'get_unique_metric_names',
        'description': 'Get unique metric names in the PDD (Physical Design Data) system.',
        'parameters': {
           'type': 'object',
            'properties': {},
        },
    },
}
def get_unique_metric_names():
    """Fetch and return unique metric names in PDD

    Returns:
        A JSON string containing all unique metric names.
    """
    endpoint = f'/v1/api/report/unique_metric_names'
    return _call_pdd_api(endpoint, f'retrieving unique metric names in PDD')

#############################################################################
# Helper function for POST requests
#############################################################################
def _call_pdd_api_post(endpoint, payload, operation_name):
    """Generic helper to call PDD (Physical Design Data) API endpoints using POST.
    
    Args:
        endpoint: URL path relative to base
        payload: Dictionary to send as JSON body
        operation_name: Human-readable operation name for logging
        
    Returns:
        JSON string with the API response or error
    """
    LOGGER.debug(f"{operation_name}")
    try:
        url = f'https://ui-api.pdd.altera.com/{endpoint}'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10, proxies={'http': "", 'https': ""}, verify=False)
        response.raise_for_status()
        
        result = response.json()
        LOGGER.debug(f"{operation_name} succeeded.")
        return json.dumps(result)
    except requests.exceptions.Timeout:
        error_msg = f'Request timed out while {operation_name}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except requests.exceptions.ConnectionError as e:
        error_msg = f'Connection error while {operation_name}: {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except requests.exceptions.HTTPError as e:
        error_msg = f'HTTP error while {operation_name}: {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})
    except Exception as e:
        error_msg = f'Failed to {operation_name}: {e}'
        LOGGER.debug(error_msg)
        return json.dumps({'error': error_msg})

#############################################################################
# get_block_experiment_data
#
# This tool executes a REST API POST call to retrieve experiment data for blocks
# within a subsystem in the PDD (Physical Design Data) system. Returns detailed
# block information including experiment data, step data, and metrics.
#
# API Endpoint: POST https://ui-api.pdd.altera.com/v1/api/block/get_multiple_block_data
# Request Body:
# {
#   "subsystem_uuid": "{subsystem_uuid}",
#   "experiment_tags": ["{experiment_tag}"]
# }
#
# Expected Response includes blocks with experiment_data, step_data, and metric_data.
#
#############################################################################
get_subsystem_block_metrics_data_dict = {
    'type': 'function',
    'function': {
        'name': 'get_subsystem_block_metrics_data',
        'description': 'Get detailed metrics data for block(s) in a subsystem in the PDD (Physical Design Data) system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subsystem_uuid': {
                    'type': 'string',
                    'description': 'The UUID of the subsystem (can be obtained from get_subsystem_uuid or get_subsystem_list)',
                    'required': True,
                },
                'block_name': {
                    'type': 'string',
                    'description': 'Only specific block data will be returned if this is specified.  None will return all (default: None)',
                    'required': False,
                },
                'experiment_tag': {
                    'type': 'string',
                    'description': 'The experiment tag to filter by (default: None)',
                    'required': False,
                },
            },
        },
    }
}
def get_subsystem_block_metrics_data(subsystem_uuid, block_name=None, experiment_tag=None):
    """Fetch and return metrics data for blocks in a subsystem.

    Args:
        subsystem_uuid: The UUID of the subsystem
        block_name: The name of the block to filter by (default: None)
        experiment_tag: The experiment tag to filter by (default: None)
        
    Returns:
        A JSON string containing block experiment data with metrics and step information.
    """
    if experiment_tag is not None and (experiment_tag.lower() == 'best' or experiment_tag.lower() == 'latest'):
        experiment_tag = None
    payload = {
        'subsystem_uuid': subsystem_uuid,
        'experiment_tags': [experiment_tag] if experiment_tag else []
    }
    data = _call_pdd_api_post('v1/api/block/get_multiple_block_data', payload, 
                             f'retrieving experiment data for subsystem {subsystem_uuid} with tag {experiment_tag}')
    if 'error' in data:
        return data
    
    # Parse the JSON data
    data_json = json.loads(data)
    
    # Loop through each block and clean up experiment_data
    for block in data_json.get("blocks", []):
        exp_data_json = block.get("experiment_data", [])
        cleaned_exp_data = []
        for exp_data in exp_data_json:
            # Remove unwanted keys from each experiment data item
            cleaned_exp = {k: v for k, v in exp_data.items() if k not in ['custom_name', 'owner_idsid', 'path']}
            cleaned_exp_data.append(cleaned_exp)
        block["experiment_data"] = cleaned_exp_data
    
    # Convert back to JSON string and clean up blocks
    data = json.dumps(data_json)
    data = _clean_up_json(data, "blocks", ['id', 'custom_name', 'start_date', 'created_by'])
    list_block = []
    if block_name is not None:
        data_json = json.loads(data)
        #print(data[:100])
        for block in data_json:
            if block["name"]==block_name:
                list_block.append(block)
        return json.dumps(list_block)
    return data
#############################################################################
# get_executive_summary
#
# This tool executes a REST API POST call to retrieve executive summary view data
# from the PDD (Physical Design Data) system. Returns high-level summary data
# filtered by experiment tag.
#
# API Endpoint: POST https://ui-api.pdd.altera.com/v1/api/executive_view_data
# Request Body:
# {
#   "experiment_data_type": "{experiment_tag}"
# }
#
#############################################################################
get_executive_summary_dict = {
    'type': 'function',
    'function': {
        'name': 'get_executive_summary',
        'description': 'Get executive summary view data from the PDD (Physical Design Data) system, filtered by experiment tag.',
        'parameters': {
            'type': 'object',
            'properties': {
                'experiment_tag': {
                    'type': 'string',
                    'description': 'The experiment tag to filter by (default: latest)',
                    'required': False,
                },
            },
        },
    }
}
def get_executive_summary(experiment_tag='latest'):
    """Fetch and return executive summary view data.
    
    Args:
        experiment_tag: The experiment tag to filter by (default: 'latest')
        
    Returns:
        A JSON string containing executive summary data for the specified experiment tag.
    """
    payload = {
        'experiment_data_type': experiment_tag
    }
    data = _call_pdd_api_post('v1/api/executive_view_data', payload, 
                             f'retrieving executive summary for experiment tag {experiment_tag}')
    data = _clean_up_json(data, None, ['experimentId'])
    return data
    # for experiment_dct in data_json:
    #     if isinstance(experiment_dct, dict):
    #         _ = experiment_dct.pop('experimentId', None)
    # return json.dumps(data_json)
    
#############################################################################
llm_dict = {
    'type': 'function',
    'function': {
        'name': 'llm',
        'description': 'As a Q&A LLM agent, help answer the query/prompt.',
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
# Automatically get all the global variables which match *_dict into a list
all_tools = [v for k, v in globals().items() if isinstance(v, dict) and k.endswith('_dict')]

def print_all_tools():
    """Print all available tools with their descriptions and parameters."""
    print("=================================================")
    for tool in all_tools:
        print(f"Tool name: {tool['function']['name']}")
        print(f"Tool description: {tool['function']['description']}")
        print(f"Tool parameters: {tool['function']['parameters']}")
        print("=================================================")
