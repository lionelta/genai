#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
"""
ask_adm.py

Lightweight CLI (patterned after ask_ddv.py) to interact with the ADM / Gatekeeper
preserved models tool (get_preserved_models) exposed in toolfiles/ask_gk_toolfile.py.

Typical natural language queries you can try (also see --examples):
  - list all preserved models
  - show preserved models limit 10
  - get preserved models for domain DV milestone 0.5a limit 15
  - list preserved models source dropbox
  - give me preserved models with name foo limit 5

If the ToolAgent does not detect a matching tool call, the query is dispatched
as plain chat to the fallback ChatbotAgent.
"""

import os
import sys
import json
import argparse
import logging
import warnings
from pprint import pformat

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, rootdir)

# Lazy import project utilities / agents (mirrors ask_ddv structure)
from lib.agents.tool_agent import ToolAgent
from lib.agents.chatbot_agent import ChatbotAgent
import lib.genai_utils as gu

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Provide default OLLAMA_HOST if not already set (mirrors ask_ddv behavior)
if 'OLLAMA_HOST' not in os.environ:
    try:
        os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']
    except Exception:
        pass


def examples() -> str:
    return (
        "Preserved Models Queries:\n"
        "- list all preserved models\n"
        "- show preserved models for domain DV \n"
        "- get preserved models milestone 0.5a \n"
        "- list preserved models source dropbox milestone 0.5a\n"
        "- is km_xcvr_common-a0-25ww39a	a preserved model\n"
       # "- list preserved models source syncpoint domain Logical_FC\n"
       # "- show preserved models domain DV milestone 0.5a name bar\n"
       # "\nTool Parameters (mapped automatically by the LLM):\n"
       # "  filter_domain      (substring match, optional)\n"
       # "  filter_milestone   (substring match, optional)\n"
       # "  filter_name        (substring match, optional)\n"
       # "  source             (dropbox | syncpoint | both)\n"
       # "  limit              (integer)\n"
    )


def print_examples():
    print(examples())


def convert_to_markdown(data, title=None):
    """Simplified markdown converter (subset of ask_ddv.convert_to_markdown)."""
    lines = []
    if title:
        lines.append(f"# {title}")
        lines.append("")

    # If raw string contains JSON, attempt to parse
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            pass  # leave as plain string

    def esc(s: str) -> str:
        if not isinstance(s, str):
            s = str(s)
        # Minimal escaping for pipes & backticks
        return s.replace('|', '\\|').replace('`', '\\`')

    if isinstance(data, dict):
        # Special-case known shape from get_preserved_models
        summary = data.get('summary')
        models = data.get('models')
        if summary and isinstance(models, list):
            lines.append('## Summary')
            for k, v in summary.items():
                if isinstance(v, dict):
                    lines.append(f"- **{esc(k)}**:")
                    for sk, sv in v.items():
                        lines.append(f"  - {esc(sk)}: {esc(sv)}")
                else:
                    lines.append(f"- **{esc(k)}**: {esc(v)}")
            lines.append("")
            lines.append('## Models')
            if not models:
                lines.append('*No models returned*')
            else:
                # Table header - updated to match new field structure
                header_cols = ['name', 'dropbox', 'syncpoint', 'sources']
                lines.append('| ' + ' | '.join(header_cols) + ' |')
                lines.append('|' + '|'.join(['---'] * len(header_cols)) + '|')
                for m in models:
                    row = []
                    for col in header_cols:
                        val = m.get(col, '')
                        if isinstance(val, list):
                            val = ', '.join(val)
                        row.append(esc(val))
                    lines.append('| ' + ' | '.join(row) + ' |')
        else:
            # Generic dict pretty-print
            for k, v in data.items():
                lines.append(f"- **{esc(k)}**: {esc(v)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append('- ' + esc(json.dumps(item)[:120]) + ('...' if len(json.dumps(item)) > 120 else ''))
            else:
                lines.append(f'- {esc(item)}')
    else:
        lines.append(esc(str(data)))

    return '\n'.join(lines) + '\n'


def dispatch_to_chatbot_agent(query):
    ca = ChatbotAgent()
    ca.kwargs['messages'] = [{'role': 'user', 'content': query}]
    ca.kwargs['stream'] = False
    res = ca.run()
    print(res.message.content)
    return res.message.content


def main(args):
    if args.examples:
        print_examples()
        return True

    os.environ['AZURE_OPENAI_API_KEY'] = os.getenv('AZURE_OPENAI_API_KEY', 'show me the money')
    os.environ['AZURE_OPENAI_MODEL'] = os.getenv('AZURE_OPENAI_MODEL', 'gpt-4.1')

    LOGGER = logging.getLogger()
    level = logging.CRITICAL
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=level)
    LOGGER.setLevel(level)

    if not args.query:
        # Fallback to examples if no query provided
        print("No query provided. Showing examples:\n")
        print_examples()
        return True

    a = ToolAgent()
    # Point specifically to the slimmer ADM-only toolfile
    a.toolfile = os.path.join(rootdir, 'toolfiles', 'ask_adm_toolfile.py')
    a.kwargs['messages'] = [{'role': 'user', 'content': args.query}]

    if args.debug:
        print('Loading toolfile and listing tools (debug mode)...')
        tf = a.load_toolfile()
        tf.print_all_tools()

    res = a.run()

    if args.debug:
        print('=================================================')
        print('Question: ', args.query)
        print('Raw LLM response deciding on tool call:')
        print(res)
        print('=================================================')

    called_tool = a.get_called_tools(res)
    if args.debug:
        print(f"called_tool: {pformat(called_tool)}")

    # If no tool call recognized, dispatch to generic chatbot
    if not called_tool or not a.is_function_name_in_loaded_tools(called_tool['function']):
        if args.debug:
            print('No matching tool call; dispatching to chatbot agent.')
        dispatch_to_chatbot_agent(args.query)
        return True

    # Handle any missing params by prompting (interactive fallback)
    if called_tool.get('missing_params'):
        a.kwargs['messages'].append({'role': 'assistant', 'content': 'missing_params:' + str(called_tool['missing_params'])})
        for key in called_tool['missing_params']:
            value = input(f"please provide the missing parameters({key}): ")
            a.kwargs['messages'].append({'role': 'user', 'content': f" parameter({key}): {value} "})

    # Re-run with parameters included
    res = a.run()
    if args.debug:
        print(f"Post-parameter tool selection response: {res}")

    # Execute tool
    tool_outputs = a.call_tool(res)
    if args.debug:
        print(f"Executed tool outputs: {tool_outputs}")
        print('=================================================')

    # tool_outputs may be a list (as per ToolAgent), handle gracefully
    if isinstance(tool_outputs, list) and len(tool_outputs) == 1:
        tool_result = tool_outputs[0]
    else:
        tool_result = tool_outputs

    md = convert_to_markdown(tool_result, title='Preserved Models Result')
    print(md)
    return True


if __name__ == '__main__':
    settings = gu.load_default_settings()

    class MyFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
        pass

    parser = argparse.ArgumentParser(prog='ask_adm.py', formatter_class=MyFormatter)
    parser.add_argument('--debug', action='store_true', default=False, help='Debug mode')
    parser.add_argument('-q', '--query', default=None, help='Query string (natural language)')
    parser.add_argument('--examples', default=False, action='store_true', help='Show example queries')
    args = parser.parse_args()

    main(args)
