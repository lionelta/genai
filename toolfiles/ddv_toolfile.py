#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
import sys
import re
import os

import subprocess
import requests
import json
rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils

# Base URL for the DDV API
DDV_BASE_URL = "https://ascyv00020.sc.altera.com:8011"



#############################################################################
get_dmxdata_versions_dict = {
    'type': 'function',
    'function': {
        'name': 'get_dmxdata_versions',
        'description': 'Get all available dmxdata/ddv versions in the system',
        'parameters': {
            'type': 'object',
            'properties': {},
        },
    }
}
def get_dmxdata_versions():
    """Get all available DMXdata versions"""
    try:
        response = requests.get(f"{DDV_BASE_URL}/dmxdata", verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get DMXdata versions: {response.status_code}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

#############################################################################
get_families_and_projects_dict = {
    'type': 'function',
    'function': {
        'name': 'get_families_and_projects',
        'description': 'Get all families and their associated projects for a specific DDV version',
        'parameters': {
            'type': 'object',
            'properties': {
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                }
            },
        },
    }
}
def get_families_and_projects(version="current"):
    """Get families and projects for a DDV version"""
    try:
        response = requests.get(f"{DDV_BASE_URL}/dmxdata/{version}/families-projects", verify=False)
        if response.status_code == 200:
            #return response.json().keys()
            return response.json()
        else:
            return {"error": f"Failed to get families and projects: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

#############################################################################
get_ip_types_dict = {
    'type': 'function',
    'function': {
        'name': 'get_ip_types',
        'description': 'Get all IP types available for each family in a specific DDV version',
        'parameters': {
            'type': 'object',
            'properties': {
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                }
            },
        },
    }
}
def get_ip_types(version="current"):
    """Get IP types for a DDV version"""
    try:
        response = requests.get(f"{DDV_BASE_URL}/dmxdata/{version}/ip-types", verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get IP types: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


#############################################################################
get_all_checkers_by_milestone_dict = {
    'type': 'function',
    'function': {
        'name': 'get_all_checkers_by_milestone',
        'description': 'Get all checkers organized by milestone for a specific IP type, device, family, and view',
        'parameters': {
            'type': 'object',
            'properties': {
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': f'The family name (e.g., {get_families_and_projects().keys()})',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': f'The device name (e.g., {get_families_and_projects().values()})',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type (e.g., "default", "asic", "soft")',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name (e.g., "default", "rtl", "pnr")',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}


def get_all_checkers_by_milestone(family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """Get all checkers organized by milestone"""
    try:
        response = requests.get(f"{DDV_BASE_URL}/dmxdata/{version}/{family}/{device}/{ip_type}/{view}", verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get design data: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

# Method to get all unique checkers from all milestones
def get_all_unique_checker(family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Returns a set of all unique checkers from all milestones in get_all_checkers_by_milestone().
    """
    data = get_all_checkers_by_milestone(family=family, device=device, ip_type=ip_type, view=view, version=version)
    checkers = data.get('checkers', {})
    unique_checkers = set()
    for checker_list in checkers.values():
        unique_checkers.update(checker_list)
    return unique_checkers


# New method to get all checkers for a given milestone
def get_checkers_by_milestone(milestone, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Returns all checkers for the given milestone from get_all_checkers_by_milestone().
    If the milestone doesn't exist or returns empty results, returns available milestones.
    Example: get_checkers_by_milestone('PHYS0.3')
    """
    data = get_all_checkers_by_milestone(family=family, device=device, ip_type=ip_type, view=view, version=version)
    checkers = data.get('checkers', {})
    
    # Get available milestones for case-insensitive matching
    available_milestones = list(checkers.keys())
    
    # Find case-insensitive match
    matched_milestone = None
    for available_milestone in available_milestones:
        if milestone.lower() == available_milestone.lower():
            matched_milestone = available_milestone
            break
    
    # Check if milestone exists and has checkers
    if matched_milestone:
        milestone_checkers = checkers.get(matched_milestone, [])
        if milestone_checkers:
            return milestone_checkers
    
    # If milestone doesn't exist or is empty, return available milestones
    return {
        "error": f"Milestone '{milestone}' not found or has no checkers",
        "available_milestones": available_milestones,
        "suggestion": f"Please use one of the available milestones: {', '.join(available_milestones)}"
    }

# Method to compare the difference between two milestones' checkers
def compare_milestone_checkers(milestone1, milestone2, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Compare the checkers between two milestones and return the difference.
    Returns a dict with keys: 'only_in_milestone1', 'only_in_milestone2', 'in_both'
    If either milestone doesn't exist, returns available milestones.
    """
    data = get_all_checkers_by_milestone(family=family, device=device, ip_type=ip_type, view=view, version=version)
    checkers = data.get('checkers', {})
    
    # Get available milestones for error handling and case-insensitive matching
    available_milestones = list(checkers.keys())
    
    # Find case-insensitive matches for both milestones
    matched_milestone1 = None
    matched_milestone2 = None
    
    for available_milestone in available_milestones:
        if milestone1.lower() == available_milestone.lower():
            matched_milestone1 = available_milestone
        if milestone2.lower() == available_milestone.lower():
            matched_milestone2 = available_milestone
    
    # Check if milestone1 exists and has checkers
    if not matched_milestone1 or not checkers.get(matched_milestone1, []):
        return {
            "error": f"Milestone '{milestone1}' not found or has no checkers",
            "available_milestones": available_milestones,
            "suggestion": f"Please use one of the available milestones: {', '.join(available_milestones)}"
        }
    
    # Check if milestone2 exists and has checkers
    if not matched_milestone2 or not checkers.get(matched_milestone2, []):
        return {
            "error": f"Milestone '{milestone2}' not found or has no checkers",
            "available_milestones": available_milestones,
            "suggestion": f"Please use one of the available milestones: {', '.join(available_milestones)}"
        }
    
    # Both milestones exist, proceed with comparison using matched milestone names
    set1 = set(checkers.get(matched_milestone1, []))
    set2 = set(checkers.get(matched_milestone2, []))
    return {
        'milestone1': matched_milestone1,  # Show the actual milestone name used
        'milestone2': matched_milestone2,  # Show the actual milestone name used
        'only_in_milestone1': list(set1 - set2),
        'only_in_milestone2': list(set2 - set1),
        'in_both': list(set1 & set2)
    }


#############################################################################
get_deliverable_info_dict = {
    'type': 'function',
    'function': {
        'name': 'get_deliverable_info',
        'description': 'Get detailed information about a specific deliverable including patterns, file types, and associated checkers',
        'parameters': {
            'type': 'object',
            'properties': {
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The device family (e.g., "Km", "Agilex")',
                    'default': 'Km',
                    'required': False,
                },
                'deliverable': {
                    'type': 'string',
                    'description': 'The deliverable name (e.g., "rtl", "syn", "pnr")',
                    'required': True,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name (optional, for device-specific deliverable info)',
                    'default': 'KM6',
                    'required': False,
                }
            },
        },
    }
}
def get_deliverable_info(deliverable, family="Km", version="current", device="KM6"):
    """Get detailed information about a deliverable"""
    try:
        if device:
            response = requests.get(f"{DDV_BASE_URL}/dmxdata/{version}/{family}/{device}/deliverable/{deliverable}", verify=False)
        else:
            response = requests.get(f"{DDV_BASE_URL}/dmxdata/{version}/{family}/deliverable/{deliverable}", verify=False)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get deliverable info: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

#############################################################################
get_checker_info_dict = {
    'type': 'function',
    'function': {
        'name': 'get_checker_info',
        'description': 'Get detailed information about a specific checker by flow and subflow',
        'parameters': {
            'type': 'object',
            'properties': {
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The device family (e.g., "Km", "Agilex")',
                    'default': 'Km',
                    'required': False,
                },
                'flow': {
                    'type': 'string',
                    'description': 'The checker flow name',
                    'required': True,
                },
                'subflow': {
                    'type': 'string',
                    'description': 'The checker subflow name',
                    'required': True,
                }
            },
        },
    }
}
def get_checker_info(flow, subflow, family="Km", version="current"):
    """Get detailed information about a checker"""
    try:
        response = requests.get(f"{DDV_BASE_URL}/dmxdata/{version}/{family}/checker", 
                              params={'flow': flow, 'subflow': subflow}, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get checker info: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

# Function to parse checker string and return its components
def parse_checker_string(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Loop through all checkers and if checker_str is a substring, parse and return components.
    Returns list of dicts: [{'checker': ..., 'deliverable': ..., 'stage_name': ..., 'flow': ..., 'subflow': ...}, ...]
    If no matches, returns an empty list.
    """
    all_checkers = get_all_unique_checker(family=family, device=device, ip_type=ip_type, view=view, version=version)
    pattern = r'^(?P<deliverable>[^_]+)__(?P<stage_name>[^\(]+)\((?P<flow>[^:]+):(?P<subflow>[^\)]+)\)$'
    matches = []
    
    for checker in all_checkers:
        if checker_str in checker:
            match = re.match(pattern, checker)
            if match:
                result = {'checker': checker}
                result.update(match.groupdict())
                matches.append(result)
            else:
                # If doesn't match expected format, still include the checker name
                matches.append({'checker': checker})
    
    return matches

# Function to get detailed checker info for a parsed checker string
def get_detailed_checker_info(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Parse checker_str using parse_checker_string, then get detailed info for each checker using get_checker_info.
    Returns list of dicts with parsed components and detailed checker info.
    """
    parsed_checkers = parse_checker_string(checker_str, family, device, ip_type, view, version)
    detailed_info = []
    
    for checker_data in parsed_checkers:
        if 'flow' in checker_data and 'subflow' in checker_data:
            checker_info = get_checker_info(checker_data['flow'], checker_data['subflow'], family, version)
            result = checker_data.copy()
            result['checker_details'] = checker_info
            detailed_info.append(result)
        else:
            # If no flow/subflow, just return the parsed data
            detailed_info.append(checker_data)
    
    return detailed_info

# Function to get the iptypes that need to run for the checker
def get_checker_iptypes(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Get the iptypes that need to run for the checker using get_detailed_checker_info.
    Returns a list of iptypes for each matching checker.
    """
    detailed_info = get_detailed_checker_info(checker_str, family, device, ip_type, view, version)
    iptypes_list = []
    
    for checker_data in detailed_info:
        if 'checker_details' in checker_data and checker_data['checker_details']:
            iptypes = checker_data['checker_details'].get('Iptypes', [])
            iptypes_list.append({
                'checker': checker_data['checker'],
                'iptypes': iptypes
            })
    
    return iptypes_list

# Function to get the owner for the checker
def get_checker_owner(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Get the owner for the checker using get_detailed_checker_info.
    Returns a list of owners for each matching checker.
    """
    detailed_info = get_detailed_checker_info(checker_str, family, device, ip_type, view, version)
    owner_list = []
    
    for checker_data in detailed_info:
        if 'checker_details' in checker_data and checker_data['checker_details']:
            owner = checker_data['checker_details'].get('Owner Email', '')
            userid = checker_data['checker_details'].get('Unix Userid', '')
            owner_list.append({
                'checker': checker_data['checker'],
                'owner': owner,
                'userid': userid
            })
    
    return owner_list

# Function to get the release requirement for the checker
def get_checker_release_requirement(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Get the release requirement for the checker using get_detailed_checker_info.
    Returns a list of release requirements for each matching checker.
    """
    detailed_info = get_detailed_checker_info(checker_str, family, device, ip_type, view, version)
    requirement_list = []
    for checker_data in detailed_info:
        if 'checker_details' in checker_data and checker_data['checker_details']:
            requirement = checker_data['checker_details'].get('Release Requirement', '')
            requirement_list.append({
                'checker': checker_data['checker'],
                'release_requirement': requirement
            })
    return requirement_list

# Function to get the documentation for the checker
def get_documentation(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Get the documentation for the checker using get_detailed_checker_info.
    Returns a list of documentation for each matching checker.
    """
    detailed_info = get_detailed_checker_info(checker_str, family, device, ip_type, view, version)
    documentation_list = []
    for checker_data in detailed_info:
        if 'checker_details' in checker_data and checker_data['checker_details']:
            documentation = checker_data['checker_details'].get('Documentation', '')
            documentation_list.append({
                'checker': checker_data['checker'],
                'documentation': documentation
            })
    return documentation_list

# Function to get the milestones that a checker needs to run for
def get_checker_milestones(checker_str, family="Km", device="KM6", ip_type="default", view="default", version="current"):
    """
    Get all milestones that a particular checker needs to run for.
    Returns a list of milestones for each matching checker.
    """
    data = get_all_checkers_by_milestone(family=family, device=device, ip_type=ip_type, view=view, version=version)
    checkers = data.get('checkers', {})
    milestone_list = []
    
    # Get all unique checkers first to find exact matches
    all_checkers = get_all_unique_checker(family=family, device=device, ip_type=ip_type, view=view, version=version)
    
    # Find matching checkers
    matching_checkers = [checker for checker in all_checkers if checker_str in checker]
    
    for matching_checker in matching_checkers:
        milestones = []
        for milestone, checker_list in checkers.items():
            if matching_checker in checker_list:
                milestones.append(milestone)
        
        milestone_list.append({
            'checker': matching_checker,
            'milestones': milestones
        })
    
    return milestone_list

get_checker_milestones_dict = {
    'type': 'function',
    'function': {
        'name': 'get_checker_milestones',
        'description': 'Get all milestones that a particular checker needs to run for',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_checkers_by_milestone_dict = {
    'type': 'function',
    'function': {
        'name': 'get_checkers_by_milestone',
        'description': 'Get all checkers for a specific milestone from get_design_data_by_ip_type',
        'parameters': {
            'type': 'object',
            'properties': {
                'milestone': {
                    'type': 'string',
                    'description': 'The milestone name (e.g., "PHYS0.3", "RTL0.5")',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_all_unique_checker_dict = {
    'type': 'function',
    'function': {
        'name': 'get_all_unique_checker',
        'description': 'Get all unique checkers from all milestones',
        'parameters': {
            'type': 'object',
            'properties': {
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

compare_milestone_checkers_dict = {
    'type': 'function',
    'function': {
        'name': 'compare_milestone_checkers',
        'description': 'Compare the checkers between two milestones and return the difference',
        'parameters': {
            'type': 'object',
            'properties': {
                'milestone1': {
                    'type': 'string',
                    'description': 'The first milestone name',
                    'required': True,
                },
                'milestone2': {
                    'type': 'string',
                    'description': 'The second milestone name',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

parse_checker_string_dict = {
    'type': 'function',
    'function': {
        'name': 'parse_checker_string',
        'description': 'Parse checker string to find matching checkers and extract their components',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_detailed_checker_info_dict = {
    'type': 'function',
    'function': {
        'name': 'get_detailed_checker_info',
        'description': 'Get detailed information about checkers matching the checker string',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_checker_iptypes_dict = {
    'type': 'function',
    'function': {
        'name': 'get_checker_iptypes',
        'description': 'Get the iptypes that need to run for the checker',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_checker_owner_dict = {
    'type': 'function',
    'function': {
        'name': 'get_checker_owner',
        'description': 'Get the owner for the checker',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_checker_release_requirement_dict = {
    'type': 'function',
    'function': {
        'name': 'get_checker_release_requirement',
        'description': 'Get the release requirement for the checker',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}

get_documentation_dict = {
    'type': 'function',
    'function': {
        'name': 'get_documentation',
        'description': 'Get the documentation for the checker',
        'parameters': {
            'type': 'object',
            'properties': {
                'checker_str': {
                    'type': 'string',
                    'description': 'The checker string to search for',
                    'required': True,
                },
                'version': {
                    'type': 'string',
                    'description': 'The DDV version (e.g., "current", "23.4.001")',
                    'default': 'current',
                    'required': False,
                },
                'family': {
                    'type': 'string',
                    'description': 'The family name',
                    'default': 'Km',
                    'required': False,
                },
                'device': {
                    'type': 'string',
                    'description': 'The device name',
                    'default': 'KM6',
                    'required': False,
                },
                'ip_type': {
                    'type': 'string',
                    'description': 'The IP type',
                    'default': 'default',
                    'required': False,
                },
                'view': {
                    'type': 'string',
                    'description': 'The view name',
                    'default': 'default',
                    'required': False,
                }
            },
        },
    }
}
#############################################################################

#print(get_checker_info("vcs", "vcs_elab"))
#print(get_all_unique_checker())
#print(parse_checker_string('vc_lint'))
#print(get_detailed_checker_info('vc_lint'))
#print(get_checker_iptypes('vc_lint'))
#print(get_deliverable_info('cthfe'))
      
# Automatically get all the global variables which match *_dict into a list
all_tools = [v for k, v in globals().items() if isinstance(v, dict) and k.endswith('_dict')]

def print_all_tools():
    print("=================================================")
    for tool in all_tools:
        print(f"Tool name: {tool['function']['name']}")
        print(f"Tool description: {tool['function']['description']}")
        print(f"Tool parameters: {tool['function']['parameters']}")
        print("=================================================")
