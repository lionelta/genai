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

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

from lib.agents.tool_agent import ToolAgent
from lib.agents.chatbot_agent import ChatbotAgent

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'


def main(args):

    if args.examples:
        print_examples()
        return True

    os.environ['AZURE_OPENAI_API_KEY'] = os.getenv("AZURE_OPENAI_API_KEY", 'show me the money')
    os.environ['AZURE_OPENAI_MODEL'] = os.getenv("AZURE_OPENAI_MODEL", 'gpt-4.1')

    LOGGER = logging.getLogger()
    level = logging.CRITICAL # to suppress all logs
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    a = ToolAgent()
    a.toolfile = os.path.join(rootdir, 'toolfiles', 'ddv_toolfile.py')
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]

    ### Print out all the toolfile loaded agents
    if args.debug:
        print("These are all the available tools:")
        tf = a.load_toolfile()
        tf.print_all_tools()

    res = a.run()
    #ani.stop()



    if args.debug:
        print("=================================================")
        print("Question: ", args.query)
        print("=================================================")
        print(f'response from LLM: {res}')
        print("=================================================")
  
    ### Dispatch query to chatbot agent if no matching tool calls are found
    called_tool = a.get_called_tools(res)
    if args.debug:
        print(f"called_tool: {pformat(called_tool)}")
    if not called_tool or not a.is_function_name_in_loaded_tools(called_tool['function']):
        dispatch_to_chatbot_agent(args.query)
        sys.exit()
    
    if called_tool['missing_params']:
        a.kwargs['messages'].append({'role': 'assistant', 'content': 'missing_params:' + str(called_tool['missing_params'])})
        for key in called_tool['missing_params']:
            value = input(f"please provide the missing parameters({key}): ")
            a.kwargs['messages'].append({'role': 'user', 'content': f" parameter({key}): {value} "})

    #pprint(a.kwargs['messages'])
    res = a.run()
    
    if args.debug:
        print(f"Response from tool: {res}")

    reslist = a.call_tool(res)
    if args.debug:
        print(f"Response from execute tool: {reslist}")
        print("=================================================")
    #dispatch_to_chatbot_agent("Tool call output: " + str(reslist) + '. Provide the markdown format for the tool output. Do not add your answer, just provide the markdown format for the tool output.')
    print(convert_to_markdown(reslist))
    #dispatch_to_chatbot_agent_markdown(str(reslist), args.query)
    #print(reslist)

def convert_to_markdown(input_data, title=None, data_type="general"):
    """
    Convert input data to markdown format optimized for web display.
    
    Args:
        input_data: The input data to convert (string, list, dict, etc.)
        title: Optional title for the markdown document
        data_type: Type hint for formatting ("table", "list", "code", "general")
    
    Returns:
        str: Formatted markdown string optimized for web rendering
    """
    markdown_output = []
    
    # Add title if provided with proper spacing
    if title:
        markdown_output.append(f"# {title}")
        markdown_output.append("")  # Add blank line after title
    
    # Handle different data types
    if isinstance(input_data, dict):
        if data_type == "table":
            # Convert dict to table format with better alignment
            markdown_output.append("| Key | Value |")
            markdown_output.append("|-----|-------|")
            for key, value in input_data.items():
                # Escape special markdown characters and handle multiline values
                key_str = _escape_markdown(str(key))
                value_str = _format_value_for_table(value)
                markdown_output.append(f"| {key_str} | {value_str} |")
        else:
            # Check if this is a simple list-like dictionary (all values are simple strings/numbers)
            is_simple_list = all(isinstance(v, (str, int, float, bool)) and not isinstance(v, bool) or v is None 
                                 for v in input_data.values())
            
            if is_simple_list and len(input_data) > 3:
                # Format as a simple list when dictionary contains just simple key-value pairs
                markdown_output.append("**Items:**")
                for key, value in input_data.items():
                    key_str = _escape_markdown(str(key))
                    if value is None or value == "":
                        markdown_output.append(f"- {key_str}")
                    else:
                        value_str = _escape_markdown(str(value))
                        markdown_output.append(f"- {key_str}: {value_str}")
            else:
                # Convert dict to well-structured definition list with better formatting
                for i, (key, value) in enumerate(input_data.items()):
                    key_str = _escape_markdown(str(key))
                    
                    if isinstance(value, list):
                        # Handle lists in dictionaries with proper bullet points
                        if len(value) > 0:
                            markdown_output.append(f"**{key_str}**:")
                            for item in value:
                                formatted_item = _format_value_for_web(item)
                                markdown_output.append(f"  - {formatted_item}")
                        else:
                            markdown_output.append(f"**{key_str}**: *empty list*")
                        
                    elif isinstance(value, dict):
                        # Handle nested dictionaries with improved structure
                        if len(value) > 0:
                            markdown_output.append(f"**{key_str}**:")
                            for sub_key, sub_value in value.items():
                                sub_key_str = _escape_markdown(str(sub_key))
                                if isinstance(sub_value, list) and len(sub_value) > 1:
                                    # For nested lists, show them as sub-bullets
                                    markdown_output.append(f"  - **{sub_key_str}**:")
                                    for sub_item in sub_value:
                                        formatted_sub_item = _format_value_for_web(sub_item)
                                        markdown_output.append(f"    - {formatted_sub_item}")
                                else:
                                    sub_value_str = _format_value_for_web(sub_value)
                                    markdown_output.append(f"  - **{sub_key_str}**: {sub_value_str}")
                        else:
                            markdown_output.append(f"**{key_str}**: *empty dictionary*")
                            
                    elif value in [None, "", []]:
                        # Handle empty or None values
                        markdown_output.append(f"**{key_str}**: *not available*")
                        
                    else:
                        # Handle simple values with better formatting
                        value_str = _format_value_for_web(value)
                        # For long strings, add line breaks for readability
                        if isinstance(value, str) and len(str(value)) > 100:
                            # Split long strings into multiple lines
                            words = str(value).split()
                            lines = []
                            current_line = []
                            current_length = 0
                            
                            for word in words:
                                if current_length + len(word) + 1 > 80:  # 80 chars per line
                                    if current_line:
                                        lines.append(" ".join(current_line))
                                        current_line = [word]
                                        current_length = len(word)
                                    else:
                                        lines.append(word)
                                        current_length = 0
                                else:
                                    current_line.append(word)
                                    current_length += len(word) + 1
                            
                            if current_line:
                                lines.append(" ".join(current_line))
                            
                            markdown_output.append(f"**{key_str}**:")
                            for line in lines:
                                markdown_output.append(f"  {_escape_markdown(line)}")
                        else:
                            markdown_output.append(f"**{key_str}**: {value_str}")
                    
                    # Add spacing between major sections, but not after the last item
                    if i < len(input_data) - 1 and not is_simple_list:
                        markdown_output.append("")  # Add spacing between items
                
    elif isinstance(input_data, (list, set, tuple)):
        if data_type == "table" and input_data and isinstance(next(iter(input_data)), dict):
            # Convert list of dicts to table with proper escaping
            if input_data:
                first_item = next(iter(input_data))
                headers = list(first_item.keys())
                # Create header row with proper escaping
                escaped_headers = [_escape_markdown(str(h)) for h in headers]
                markdown_output.append("| " + " | ".join(escaped_headers) + " |")
                markdown_output.append("|" + "|".join(["-----"] * len(headers)) + "|")
                
                for item in input_data:
                    row = []
                    for header in headers:
                        value = item.get(header, "")
                        escaped_value = _escape_markdown(str(value)).replace('\n', '<br>')
                        row.append(escaped_value)
                    markdown_output.append("| " + " | ".join(row) + " |")
        else:
            # Convert list/set/tuple to bullet points with proper formatting
            # Sort if it's a set to provide consistent ordering
            items_to_process = sorted(input_data) if isinstance(input_data, set) else input_data
            
            for i, item in enumerate(items_to_process):
                if isinstance(item, dict):
                    # For dictionaries in lists, format with proper structure and indentation
                    # Use checker name as identifier if available, otherwise use generic Item number
                    item_title = item.get('checker', f"Item {i + 1}")
                    markdown_output.append(f"**{_escape_markdown(str(item_title))}:**")
                    
                    for key, value in item.items():
                        key_str = _escape_markdown(str(key))
                        
                        if isinstance(value, list):
                            # Handle nested lists
                            if len(value) > 0:
                                markdown_output.append(f"  - **{key_str}**:")
                                for sub_item in value:
                                    formatted_sub_item = _format_value_for_web(sub_item)
                                    markdown_output.append(f"    - {formatted_sub_item}")
                            else:
                                markdown_output.append(f"  - **{key_str}**: *empty list*")
                                
                        elif isinstance(value, dict):
                            # Handle nested dictionaries
                            if len(value) > 0:
                                markdown_output.append(f"  - **{key_str}**:")
                                for sub_key, sub_value in value.items():
                                    sub_key_str = _escape_markdown(str(sub_key))
                                    sub_value_str = _format_value_for_web(sub_value)
                                    markdown_output.append(f"    - **{sub_key_str}**: {sub_value_str}")
                            else:
                                markdown_output.append(f"  - **{key_str}**: *empty dictionary*")
                                
                        elif value in [None, "", []]:
                            # Handle empty or None values
                            markdown_output.append(f"  - **{key_str}**: *not available*")
                            
                        else:
                            # Handle simple values
                            value_str = _format_value_for_web(value)
                            markdown_output.append(f"  - **{key_str}**: {value_str}")
                    
                    # Add spacing between items, but not after the last item
                    if i < len(items_to_process) - 1:
                        markdown_output.append("")
                else:
                    # For non-dictionary items, use simple bullet point formatting
                    formatted_item = _format_value_for_web(item)
                    markdown_output.append(f"- {formatted_item}")
                
    elif isinstance(input_data, str):
        if data_type == "code":
            # Wrap string in code block with language detection
            language = _detect_language(input_data)
            markdown_output.append(f"```{language}")
            markdown_output.append(input_data)
            markdown_output.append("```")
        elif "\n" in input_data:
            # Multi-line string, preserve formatting with proper escaping
            escaped_content = _escape_markdown(input_data)
            markdown_output.append(escaped_content)
        else:
            # Single line string with escaping
            escaped_content = _escape_markdown(input_data)
            markdown_output.append(escaped_content)
    else:
        # Handle other types (int, float, etc.)
        if data_type == "code":
            markdown_output.append(f"```\n{input_data}\n```")
        else:
            markdown_output.append(_escape_markdown(str(input_data)))
    
    # Add final spacing for better web rendering
    result = "\n".join(markdown_output)
    if not result.endswith("\n"):
        result += "\n"
    
    return result


def _escape_markdown(text):
    """Escape special markdown characters for proper web rendering."""
    if not isinstance(text, str):
        text = str(text)
    
    # Escape markdown special characters
    special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']
    for char in special_chars:
        if char == '|':
            text = text.replace(char, '\\|')
        elif char == '\\':
            text = text.replace(char, '\\\\')
        else:
            text = text.replace(char, f'\\{char}')
    
    return text


def _format_value_for_web(value):
    """Format a value for better web display."""
    if isinstance(value, dict):
        # For nested dicts, create a compact representation
        items = [f"{_escape_markdown(str(k))}: {_escape_markdown(str(v))}" for k, v in value.items()]
        return "{" + ", ".join(items) + "}"
    elif isinstance(value, list):
        # For nested lists, create a compact representation
        items = [_escape_markdown(str(item)) for item in value]
        return "[" + ", ".join(items) + "]"
    else:
        return _escape_markdown(str(value))


def _format_value_for_table(value):
    """Format a value specifically for table cells in markdown."""
    if isinstance(value, list):
        # For lists in tables, use HTML line breaks for better rendering
        items = [_escape_markdown(str(item)) for item in value]
        return "<br>".join([f"• {item}" for item in items])
    elif isinstance(value, dict):
        # For dicts in tables, create compact key-value pairs
        items = []
        for k, v in value.items():
            key_str = _escape_markdown(str(k))
            if isinstance(v, list):
                value_str = ", ".join([_escape_markdown(str(item)) for item in v])
                items.append(f"**{key_str}**: [{value_str}]")
            else:
                value_str = _escape_markdown(str(v))
                items.append(f"**{key_str}**: {value_str}")
        return "<br>".join(items)
    else:
        # Handle simple values with proper escaping
        return _escape_markdown(str(value)).replace('\n', '<br>')


def _detect_language(code_string):
    """Simple language detection for syntax highlighting."""
    code_lower = code_string.lower().strip()
    
    # Python detection
    if any(keyword in code_lower for keyword in ['def ', 'import ', 'from ', 'print(', 'if __name__']):
        return 'python'
    
    # SQL detection
    if any(keyword in code_lower for keyword in ['select ', 'from ', 'where ', 'insert ', 'update ', 'delete ']):
        return 'sql'
    
    # JSON detection
    if code_string.strip().startswith(('{', '[')) and code_string.strip().endswith(('}', ']')):
        try:
            json.loads(code_string)
            return 'json'
        except:
            pass
    
    # Shell/Bash detection
    if any(keyword in code_lower for keyword in ['#!/bin/', 'echo ', 'ls ', 'cd ', 'mkdir ', 'rm ']):
        return 'bash'
    
    # Default to plain text
    return ''


def dispatch_to_chatbot_agent_markdown(tooloutput, user_query):
    """Dispatch the query to a chatbot agent if no tool calls are found."""
    #print("No tool calls found in the response. Dispatching to common Q&A llm agent")
    ca = ChatbotAgent()
    if not user_query: user_query = args.query
    ca.kwargs['messages'] = [{'role': 'system', 'content': f"You are an assistant that get the output from toolagent. **Tool output**{tooloutput}. Reponse to user need first complete result of tool output.{tooloutput}. Then Based on the **User Query**: {user_query} and tooloutput, answer user query, Think step by step, show numbering when involve counting."}, {'role': 'user', 'content': user_query}]
    ca.kwargs['stream'] = False
    res = ca.run()
    print(res.message.content)
    #gu.print_markdown(res.message.content, cursor_moveback=False)
    return res.message.content



def dispatch_to_chatbot_agent(query):
    """Dispatch the query to a chatbot agent if no tool calls are found."""
    #print("No tool calls found in the response. Dispatching to common Q&A llm agent")
    ca = ChatbotAgent()
    if not query: query = args.query
    ca.kwargs['messages'] = [{'role': 'user', 'content': query}]
    ca.kwargs['stream'] = False
    res = ca.run()
    print(res.message.content)
    return res.message.content

def examples():
    examples = """
Checker Information:
- give me all unique checkers
- show me checkers for PHYS0.3 milestone
- compare checkers between RTL0.5 and PHYS0.3 milestones
- find checkers matching 'vcs_elab'
- get detailed info for checker containing 'vc_lint'

Checker Properties:
- get iptypes required for checker 'cthfe__vcs_elab'
- show me owner information for checker 'vc_lint'
- get release requirement for checker 'vc_lint'
- show documentation for checker 'vc_cdc'
- get all milestones that checker 'vcs_elab' runs in

"""
    return examples

def print_examples():
    print(examples())


if __name__ == '__main__':
    settings = gu.load_default_settings()
    
    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter): pass

    parser = argparse.ArgumentParser(prog='ask_ddv.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-q', '--query', default=None, help='Query string')
    parser.add_argument('--examples', default=False, action='store_true', help='Show example queries')
    args = parser.parse_args()

    main(args)

