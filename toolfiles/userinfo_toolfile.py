#!/usr/bin/env python

import subprocess
import json
import sys
import os
import io
import csv
ROOTDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, ROOTDIR)
import lib.genai_utils
import lib.agents.base_agent

#############################################################################
get_user_groups_dict = {
    'type': 'function',
    'function': {
        'name': 'get_user_groups',
        'description': 'get the groups of a user',
        'parameters': {
            'type': 'object',
            'properties': {
                'userid': {
                    'type': 'string',
                    'description': 'The user ID to look up',
                    'required': True,
                }
            },
        },
    }
}
def get_user_groups(userid):
    exitcode, output = subprocess.getstatusoutput(f"groups {userid}")
    return output

#############################################################################
get_user_info_dict = {
    'type': 'function',
    'function': {
        'name': 'get_user_info',
        'description': 'get the information of all users from the internal user database',
        'parameters': {
            'type': 'object',
            'properties': {
                'original_raw_prompt': {
                    'type': 'string',
                    'description': 'The original raw prompt from the user',
                    'required': True,
                },
            },
        },
    }
}
def get_user_info(original_raw_prompt):
    raw_json_data = load_user_json()
    compressed = compress_raw_user_data_to_list(raw_json_data)
    csvstring = convert_list_to_csv_string(compressed)  # converting list to csvstring help saved 34k tokens (239k to 205k) 

    ba = lib.agents.base_agent.BaseAgent()
    ba.kwargs['messages'] = [
        {'role': 'user', 'content':f""" {original_raw_prompt} \n\n  {csvstring} """}
    ]
    res = ba.run()
    return res.message.content


def convert_list_to_csv_string(data):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    writer.writerows(data)
    return output.getvalue()


def load_user_json():
    data = json.load(open('/nfs/site/disks/da_infra_1/users/junweich/altera_cdislookup/emp_data.json'))
    return data

def compress_raw_user_data_to_list(raw_json_data):
    ''' so that it uses less tokens 
    original raw json data:

    {
        "12307489": {
            "EMP_IDSID": "aakanshx",
            "EMP_DISPLAY": "Choudhary, AakanshaX",
            "EMP_SURNAME": "Choudhary",
            "EMP_GIVENNAME": "Aakansha",
            "EMP_EMAIL": "AakanshaX.Choudhary@altera.com",
            "EMP_UPN": "AakanshaX.Choudhary@Altera.com",
            "EMP_STATUS": "A",
            "EMP_TYPE": "CW",
            "EMP_COUNTRY": "India",
            "EMP_DEPT": "Altera",
            "EMP_ROLE": "",
            "MGR_WWID": "12294898",
            "MGR_IDSID": "amazooch",
            "MGR_NAME": "Mazoochi, Amir",
            "MGR_EMAIL": "amir.mazoochi@altera.com",
        },
        ... ... ...
    }
    '''
    key_map = {
        "EMP_IDSID": "IDSID",
        "EMP_DISPLAY": "NAME",
        #"EMP_SURNAME": "SURNAME",
        #"EMP_GIVENNAME": "GIVENNAME",
        "EMP_EMAIL": "EMAIL",
        #"EMP_UPN": "UPN",
        #"EMP_STATUS": "STATUS",
        #"EMP_TYPE": "TYPE",
        #"EMP_COUNTRY": "COUNTRY",
        #"EMP_DEPT": "DEPT",
        #"EMP_ROLE": "ROLE",
        "MGR_WWID": "Manager_WWID",
        "MGR_IDSID": "Manager_IDSID",
        "MGR_NAME": "Manager_NAME",
        "MGR_EMAIL": "Manager_EMAIL",
    }
    compressed = []
    sortedkeys = sorted(key_map.keys())
    compressed.append(sortedkeys+["EMP_WWID"])  # header row
    for userid in raw_json_data:
        tmp = []
        for key in sortedkeys:
            tmp.append(raw_json_data[userid].get(key, ""))
        tmp.append(userid)
        compressed.append(tmp)
    return compressed

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
