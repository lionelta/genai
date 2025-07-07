#!/usr/bin/env python

import subprocess 

list_gkmodel_dict = {
    'type': 'function',
    'function': {
        'name': 'list_gkmodels',
        'description': 'Get all the available gk release model for a given repo',
        'parameters': {
            'type': 'object',
            'properties': {
                'reponame': {
                    'type': 'string',
                    'description': 'The given repo name'
                }
            },
        'required': ['reponame'],
        },
    }
}
def list_gkmodels(reponame=None):
    ret = subprocess.getoutput(f''' ls /nfs/site/disks/psg.mod.000/release/{reponame} ''')
    return f'''
```
{ret}
```
'''

#############################################################################
gkmodel_sum_dict = {
    'type': 'function',
    'function': {
        'name': 'get_gkmodel_summary',
        'description': 'Get the report/result/summary of the given gk/gatekeeper release model',
        'parameters': {
            'type': 'object',
            'properties': {
                'modname': {
                    'type': 'string',
                    'description': 'The given gk/gatekeeper release model'
                }
            },
        'required': ['modname'],
        },
    }
}
def get_gkmodel_summary(modname=None):
    reponame = modname.split('-a0-')[0]
    ret = subprocess.getoutput(f''' cat /nfs/site/disks/psg.mod.000/release/{reponame}/{modname}/GATEKEEPER/gk_report.txt  ''')
    return f'''
```
{ret}
```
'''
#############################################################################
local_disk_dict = {
    'type': 'function',
    'function': {
        'name': 'local_disk',
        'description': 'Get the $HOTEL or data path for the current user',
        'parameters': {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'string',
                    'description': 'The current user'
                }
            },
        'required': ['user'],
        },
    }
}

def local_disk(user=None):
    return f''' 
``` 
/p/psg/data/{user} 
``` '''

#############################################################################
disk_info_dict = {
    'type': 'function',
    'function': {
        'name': 'get_disk_info',
        'description': 'Get the information of the given disk',
        'parameters': {
            'type': 'object',
            'properties': {
                'disk': {
                    'type': 'string',
                    'description': 'The given disk'
                }
            },
        'required': ['disk'],
        },
    }
}
def get_disk_info(disk=None):
    ret = subprocess.getoutput(f''' stodstatus area "path=~'{disk}'" ''')
    return f''' 
``` 
{ret}
``` '''
#############################################################################
list_all_tools_dict = {
    'type': 'function',
    'function': {
        'name': 'list_all_tools',
        'description': 'Get/show all available customized tools in the system',
    }
}
def list_all_tools(disk=None):
    ret = ''
    for i, tool in enumerate(all_tools):
        ret = ret + f'{i+1}. {tool["function"]["description"]}\n'
    return f''' 
``` 
{ret}
``` '''
#############################################################################

all_tools = [local_disk_dict, disk_info_dict, gkmodel_sum_dict, list_gkmodel_dict, list_all_tools_dict]
