#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python

'''
'''
import sys
import os
import argparse
import logging
import json
import warnings
import sqlite3
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.regex_db
import tempfile
import fcntl
import re
import base64
import subprocess

warnings.simplefilter("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

PROXY_ENVVARS = ['http_proxy', 'https_proxy']

LOGGER = logging.getLogger(__name__)

def load_default_settings(infile=None):
    if infile is None:
        infile = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'genai_default_settings.json')
    with open(infile, 'r') as f:
        data = json.load(f)
    return data

def proxyon():
    for k in PROXY_ENVVARS:
        os.environ[k] = 'proxy-dmz.altera.com:912'

def proxyoff():
    for k in PROXY_ENVVARS:
        del os.environ[k]

def load_embedding_model(modelname):
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name=modelname,  model_kwargs={'trust_remote_code': True})
    return embeddings

def load_faiss_dbs(dbpaths, embedding_obj):
    from langchain_community.vectorstores import FAISS
    
    ### Load the first db
    vectorstore = FAISS.load_local(dbpaths[0], embedding_obj, allow_dangerous_deserialization=True)
    
    ### Merge the rest of the db 
    for dbpath in dbpaths[1:]:
        db = FAISS.load_local(dbpath, embedding_obj, allow_dangerous_deserialization=True)
        vectorstore.merge_from(db)
    
    return vectorstore

def load_regex_dbs(dbpaths):
    rows = []
    for dbpath in dbpaths:
        regexdbpath = os.path.join(dbpath, 'regex.db')
        try:
            db = lib.regex_db.RegexDB(regexdbpath)
            rows.extend(db.get_all_rows())
        except Exception as e:
            pass
    return rows

def get_faiss_dbs(rootdir):
    ''' the faissdbs directory should be in the rootdir, in the following structure
    <rootdir>/
        faissdbs/
            db1/
                default/
                    index.faiss
                    index.pkl
                    .description
            db2/
                default/
                    index.faiss
                    index.pkl
                    .description
            ...

    return => {
        'db1': {
            'dbpath': '/path/to/db1/default', 
            'description': 'N/A',
            'croncmd': <string> | '',
            'emails': <string> | '',
            'acg': <string> | '',
        }, 
        'db2': ... ... ...
    }
    '''
    base_dir = os.path.join(rootdir, 'faissdbs')
    faiss_dbs = {}
    for name in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, name)):
            dbpath = os.path.join(base_dir, name, 'default')
            if os.path.exists(dbpath):
                metafiles = ['.croncmd', '.emails', '.acg', '.description']
                faiss_dbs[name] = {'dbpath': dbpath}
                
                ### Initialize the meta keys
                for metafile in metafiles:
                    faiss_dbs[name][metafile[1:]] = ''

                    ### Read the meta files and update the dictionary, if they exist
                    file_path = os.path.join(dbpath, metafile)
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            faiss_dbs[name][metafile[1:]] = f.read().rstrip()
    
    return faiss_dbs


def quotify(txt):
    '''
    Handles the quoting sorcery of a string/command so that 
    it can be safely passed into another command.

    Example Of Usage:-
    ------------------
    a = """ wash -n psgeng intelall -c 'echo "a b"; groups; date' """
    b = 'arc submit -- {}'.format(quotify(a))
    c = 'arc submit -- {}'.format(quotify(b))
    os.system(c)
    '''
    new = txt.replace("'", "'\"'\"'")
    return "'{}'".format(new)

def print_markdown(text, pyg_exe=None, cursor_moveback=False, lexer='md'):
    '''
    Print the text in markdown format. 
    '''
    if pyg_exe is None:
        pyg_exe = '/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/pygmentize'

    if cursor_moveback:
        #linecount = text.count('\n')
        linecount = calculate_printed_lines(text) - 1

        ### Move cursor to the original line
        sys.stdout.write(f'\033[{linecount}A')
        sys.stdout.flush()
        
        ### Move cursor to the beginning of the line
        sys.stdout.write('\r')
        sys.stdout.flush()

    with tempfile.NamedTemporaryFile(mode='w+t', delete=True) as temp_file:
        temp_file.write(text)
        temp_file.flush()
        cmd = f'''{pyg_exe} -l {lexer} {temp_file.name}'''
        os.system(cmd)

def get_terminal_width():
    """Gets the width of the current terminal in columns."""
    try:
        if not sys.stdout.isatty():
            return None  # Not a terminal
        h, w, _, _ = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, 'HHHH')
        return w
    except Exception:
        try:
            return os.get_terminal_size().columns
        except OSError:
            return None  # Unable to get terminal size

def calculate_printed_lines(text):
    """
    Calculates the number of lines the given text will occupy when printed
    in the current Linux terminal/Konsole.
    """
    terminal_width = get_terminal_width()
    if terminal_width is None:
        # Cannot determine terminal width, assume each newline is a new line
        return text.count('\n') + 1

    lines = 0
    current_line_length = 0
    for char in text:
        if char == '\n':
            lines += 1
            current_line_length = 0
        else:
            current_line_length += 1
            if current_line_length > terminal_width:
                lines += 1
                current_line_length = 1  # Start of a new wrapped line

    # Account for the last line if it doesn't end with a newline
    if current_line_length > 0 or not text:
        lines += 1

    return lines


def extract_xml(text, tag):
    """
    Extracts the content of the first occurrence of the specified XML tag from the given text.
    Copied from Anthropic's code:
        https://github.com/anthropics/anthropic-cookbook/blob/main/patterns/agents/util.py
    """
    pattern = f'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def get_confluence_decendants_of_page(pageid, username, token):
    '''
    returns the list of child page ids of the given parent_id, hierarchically.
    '''
    endpoint = f'https://altera-corp.atlassian.net/wiki/api/v2/pages/{pageid}/descendants?limit=250&depth=5'
    credentials = f'{username}:{token}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode("ascii")
    cmd = f"""curl -s -H 'Authorization: Basic {encoded_credentials}' -H 'Content-Type: application/json' '{endpoint}' """
    LOGGER.debug(f'get_confluence_decendants_of_page cmd: {cmd}')
    output = subprocess.getoutput(cmd)
    LOGGER.debug(f'get_confluence_decendants_of_page output: {output}')
    jsondata = json.loads(output)
    LOGGER.debug(f'get_confluence_decendants_of_page jsondata count: {len(jsondata["results"])}')
    return jsondata

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] - %(levelname)s-[%(module)s]: %(message)s', level=logging.DEBUG)
    sys.exit(main())

