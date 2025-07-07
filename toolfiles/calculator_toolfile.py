#!/usr/bin/env python


#############################################################################
add3_dict = {
    'type': 'function',
    'function': {
        'name': 'add3',
        'description': 'add three numbers',
        'parameters': {
            'type': 'object',
            'properties': {
                'a': {
                    'type': 'int',
                    'description': 'The first number to add',
                    'required': True,
                },
                'b': {
                    'type': 'int',
                    'description': 'The second number to add',
                    'required': True,
                },
                'c': {
                    'type': 'int',
                    'description': 'The third number to add',
                    'required': True,
                }
            },
        },
    }
}
def add3(a, b, c):
    print("Adding three numbers:", a, b, c)
    res = int(a) + int(b) + int(c)
    print("Result:", res)
    return res

#############################################################################
subtract_dict = {
    'type': 'function',
    'function': {
        'name': 'subtract',
        'description': 'subtract two numbers',
        'parameters': {
            'type': 'object',
            'properties': {
                'a': {
                    'type': 'int',
                    'description': 'The first number to subtract',
                    'required': True,
                },
                'b': {
                    'type': 'int',
                    'description': 'The second number to subtract',
                    'required': True,
                }
            },
        },
    }
}
def subtract(a, b):
    print("Subtracting two numbers:", a, b)
    res = int(a) - int(b)
    print("Result:", res)
    return res



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
