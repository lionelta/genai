#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
Confirm Working with :-
- venv: 3.10.11_sles12_cuda
- host: asccf06294100.sc.altera.com

'''
import os
import sys
import logging
import warnings
import argparse
import importlib.util
from pprint import pprint, pformat
import threading
import itertools
import time
import subprocess
import json
import re

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from lib.agents.tool_agent import ToolAgent
from lib.agents.base_agent import BaseAgent
from lib.loading_animation import LoadingAnimation

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

LOGGER = logging.getLogger()

def main(args):

    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    os.environ['AZURE_OPENAI_MODEL'] = 'gpt-4o'

    level = logging.INFO # to suppress all logs
    if args.debug:
        level = logging.DEBUG
        logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    else:
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=level)
    LOGGER.setLevel(level)

    b = BaseAgent()
    toolagent = ToolAgent()
    toolagent.toolfile = os.path.join(rootdir, 'toolfiles', 'ask_gk_toolfile.py')
    toolfileobj = toolagent.load_toolfile()

    if args.debug:
        LOGGER.debug("These are all the available tools:")
        toolfileobj.print_all_tools()
    
    b.kwargs['messages'] = [{'role': 'user', 'content': orchestrator_prompt(args.query, toolagent.load_toolfile().all_tools)}]
    res = b.run()
    raw_plan_str = res.message.content
    plan_str = remove_newline_and_markdown(raw_plan_str)
    plan = json.loads(plan_str)
    
    gu.print_markdown(f"""
**+-----------------------------------------+**
**|              Plans From LLM:            |**
**+-----------------------------------------+**
""", cursor_moveback=False)
    gu.print_markdown(json.dumps(plan, indent=4), cursor_moveback=False, lexer='json')

    results = execute_plan(plan, toolagent)
    response = generate_final_response(args.query, plan, results)




    gu.print_markdown(f"""
**+-----------------------------------------+**
**|      Final Response to User Query       |**
**+-----------------------------------------+**
""", cursor_moveback=False)
    gu.print_markdown(response, cursor_moveback=False)
    print('=================================================')

    return True   


def generate_final_response(user_query, llm_plan, results):
    """Dispatch the query to a chatbot agent if no tool calls are found."""
    prompt = f"""You are a helpful assistant.  

    **The user query is:**  
    {user_query}

    **The planned steps are:**  
    {llm_plan}  

    **The results obtained from executing the steps are:**  
    {results}  

    Based on the above information, please provide a final concise and informative answer to the user's query.

"""
    return llm(prompt)

def execute_plan(plan, toolagent):
    results = {} # stores the results of each step

    for step_data in plan:
        step_number = step_data["step"]
        description = step_data["description"]
        function_name = step_data.get("function_name")
        raw_parameters = step_data.get("parameters", {})
        parameters = replace_params_with_steps_output(raw_parameters, results)
        agent_to_call = step_data.get("agent_to_call")
        input_to_agent = step_data.get("input_to_agent")

        LOGGER.info(f"\nExecuting Step {step_number}: {description}")

        if function_name and function_name != 'llm':
            if toolagent.is_function_name_in_loaded_tools(function_name):
                LOGGER.debug(f"Calling function: {function_name} with parameters: {parameters}")
                try:
                    output = toolagent.execute_function(function_name, **parameters)
                    results[f"step_{step_number}"] = output
                    LOGGER.debug(f"Function '{function_name}' output: {output}")
                except Exception as e:
                    error_message = f"Error executing function '{function_name}': {e}"
                    results[f"step_{step_number}"] = error_message
                    LOGGER.error(error_message)
            else:
                error_message = f"Error: Function '{function_name}' not found."
                results[f"step_{step_number}"] = error_message
                LOGGER.error(error_message)


        elif not function_name or function_name == 'llm':
            LOGGER.debug(f"Dispatching to LLM for step {step_number} with description: {description}")

            ### Call llm
            prompt = f"""Let's think step by step. Based on the planned steps, and the results obtained, please provide a direct response to the step_{step_number}, using it's "description" as the prompt.  

            DO NOT explain the steps or the reasoning behind the response. Just provide the final answer.  
            DO NOT include any markdown formatting in the response.  

            **Planned Steps:**  
            {plan}  

            **Results:**  
            {results}  

            **User Query:**  
            {description}
            """
            output = llm(prompt, role='assistant')
            results[f"step_{step_number}"] = output
            LOGGER.debug(f"LLM output for step {step_number}: {output}")

        else:
            LOGGER.debug("No function or agent call for this step.")
            results[f"step_{step_number}"] = "No action taken."

    # If no response generator was called explicitly, return all results
    return results

def replace_params_with_steps_output(params, results):
    """Replace parameters that reference previous step outputs with actual results."""
    for key, value in params.items():
        match = re.search(r'<output from step (\d+)>', value)
        if match:
            # Get the step number from the match
            step_number = match.group(1)
            step_string = f"step_{step_number}"
            if step_string in results:
                # Replace the placeholder with the actual result
                params[key] = re.sub(r'<output from step \d+>', results[step_string], value)

    return params


def llm(query, role='user'):
    """Dispatch the query to a chatbot agent if no tool calls are found."""
    ba = BaseAgent()
    ba.kwargs['messages'] = [{'role': role, 'content': query}]
    ba.kwargs['stream'] = False
    res = ba.run()
    LOGGER.debug(f" -- LLM Response: {res}")

    return res.message.content


def remove_newline_and_markdown(json_str):
    """Remove newline characters and markdown formatting from a JSON string."""
    json_str = remove_newline(json_str)
    json_str = remove_markdown(json_str)
    return json_str

def remove_newline(json_str):
    """Remove newline characters from a JSON string."""
    import re
    # Remove newline characters
    json_str = re.sub(r'\n', '', json_str)
    # Remove extra spaces
    json_str = re.sub(r'\s+', ' ', json_str)
    return json_str

def remove_markdown(json_str):
    """Remove markdown formatting from a JSON string."""
    import re
    # Remove code block start and end
    json_str = re.sub(r"```json", '', json_str)
    json_str = re.sub(r"```", '', json_str)
    # Remove inline code
    json_str = re.sub(r"`", '', json_str)
    return json_str


def orchestrator_prompt(user_query, available_functions):
    return f"""You are a planning agent. Your goal is to break down the user's query into a step-by-step plan of functions to call to answer the query.

    User Query: {user_query}

    Available Functions:
    {available_functions}

    Think step by step about how to best answer the query using the available functions. Output a JSON list of steps, where each step looks like the following:
    {{
        "step": "Step number",
        "description": "A brief description of this step",
        "function_name": "Name of the function to call (if any)",
        "parameters": {{ "param1": "value1", "param2": "value2" }} (if applicable),
    }}   

    If the parameter requires output from a previous step, use the format `<output from step X>` where X is the step number.  

    Make sure the output JSON list is well-formed and parsable.  

    If a step doesn't involve calling a function or a specialized agent directly (e.g., initial analysis), you can leave 'function_name' and 'agent_to_call' empty.

    Example Plan:
    [
        {{
            "step": 1,
            "description": "Search for information about the identified entities.",
            "function_name": "search_wikipedia",
            "parameters": {{ "query": "Tell me more about Black Pink" }},
        }},
        {{
            "step": 2,
            "description": "Summarize the search results.",
            "function_name": "summarize_text",
            "parameters": {{ "text": "<output from step 2>" }},
        }},
        {{
            "step": 3,
            "description": "Formulate the final answer based on the summary.",
            "function_name": "llm_call",
            "parameters": {{ "prompt": "<output from step 2" }},
        }}
    ]

    Your Plan (in JSON format):
    """

if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='orchestrator.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-q', '--query', default=None, help='Query string')
    args = parser.parse_args()

    main(args)

