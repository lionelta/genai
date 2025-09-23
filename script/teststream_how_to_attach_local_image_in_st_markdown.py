#!/usr/bin/env python
'''
How To Run:
    - ssh: asccf06294100.sc.altera.com
    - venv: 3.10.11_sles12_sscuda
    - proxyon
    - streamlit run --server.headless true --logger.level debug stream.py
'''

import os
import sys
import streamlit as st
try:
    del os.environ['http_proxy']
    del os.environ['https_proxy']
except:
    pass
import argparse
import logging
import datetime
import json
import copy
import extra_streamlit_components as stx
import time
import requests
import pwd
import grp
import subprocess

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

menu_items = {
    'Get Help': 'https://go2.altera.com/aichatbot_wiki',
    'About': f"If you would like to have your wikispace added to the chatbot, please contact yoke.liang.lionel.tan@altera.com or joanne.low@altera.com",
    'Report a Bug': 'mailto:joanne.low@altera.com; yoke.liang.lionel.tan@altera.com'
}
st.set_page_config(page_title='TEST', layout='wide', menu_items=menu_items)
st.title('TEST')

############################################################################
######## START: USER AUTHENTICATION ########################################
############################################################################
def loading(text):
    with st.spinner(text):
        time.sleep(2)

def get_manager():
    cm = stx.CookieManager()
    loading(f"Loading cookies {st.session_state.count} ...")
    return cm

def authenticate(userid, password):
    if not userid or not password:
        st.stop()

    url = 'https://ascyv00020.sc.altera.com:8555/api/authenticate'
    data = {"username": userid, "password": password, "redirect_success": "success_url", "redirect_fail":"fail_url"}

    #os.environ['http_proxy'] = 'http://proxy-dmz.altera.com:912'
    #os.environ['https_proxy'] = 'http://proxy-dmz.altera.com:912'
    try:
        del os.environ['http_proxy']
        del os.environ['https_proxy']
    except:
        pass
    res = requests.post(url, json=data, verify=False)
    resjson = json.loads(res.text)
    st.write(resjson)
    try:
        oneyear = datetime.datetime.now() + datetime.timedelta(days=365)
        st.session_state.cm.set('userid', resjson['idsid'], expires_at=oneyear)
        loading("Logging in...")
    except:
        st.write("Failed to login")
        st.stop()

def get_user_groups(username):
    try:
        user_id = pwd.getpwnam(username).pw_uid
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        return groups
    except KeyError:
        return []

if 'count' not in st.session_state:
    st.session_state.count = 0

if 'cm' not in st.session_state:
    st.session_state.cm = get_manager()

st.session_state.count += 1

if 'userid' not in st.session_state.cm.cookies:
    userid = st.text_input("Enter your Altera Linux userid")
    password = st.text_input("Enter your password", type="password")
    authenticate(userid, password)
############################################################################
######## END: USER AUTHENTICATION ##########################################
############################################################################
    

def convert_mysql_table_to_markdown(text):
    '''
    Convert MySQL text table to markdown table
    '''
    lines = text.split('\n')
    md_lines = []
    for i, line in enumerate(lines):
        if line.startswith('+') and line.endswith('+'):
            continue
        elif line.startswith('|') and line.endswith('|'):
            cols = [col.strip() for col in line.split('|')[1:-1]]
            md_line = '| ' + ' | '.join(cols) + ' |'
            md_lines.append(md_line)
            if i == 1:
                md_lines.append('|' + ' --- |' * len(cols))
    return '\n'.join(md_lines)

def convert_mysql_table_to_panda_dataframe(text):
    '''
    Convert MySQL text table to panda dataframe
    '''
    import pandas as pd
    from io import StringIO

    lines = text.split('\n')
    data = []
    columns = []
    for i, line in enumerate(lines):
        if line.startswith('+') and line.endswith('+'):
            continue
        elif line.startswith('|') and line.endswith('|'):
            cols = [col.strip() for col in line.split('|')[1:-1]]
            if i == 1:
                columns = cols
            else:
                data.append(cols)
    df = pd.DataFrame(data, columns=columns)
    return df


############################################################################
### If reached here, user is authenticated !!!
############################################################################
rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.chatbot_agent import ChatbotAgent 

if 'OLLAMA_HOST' not in os.environ:
    os.environ['OLLAMA_HOST'] = gu.load_default_settings()['ollama_host']

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'


### LLM Settings
llm_settings = gu.load_default_settings()

faiss_dbs = gu.get_faiss_dbs(rootdir)

### Move psgcth2tfm to first element
faiss_dbs_keys = []
for k in faiss_dbs:
    if k == 'psgcth2tfm':
        faiss_dbs_keys.insert(0, k)
    else:
        faiss_dbs_keys.append(k)

version = os.path.basename(rootdir)

### Load groupdb.json file
groupdb_json = os.path.join(rootdir, 'groupdb.json')
with open(groupdb_json, 'r') as f:
    groupdb = json.load(f)
    ### Remove keys which starts with '_'
    groupdb = {k: v for k, v in groupdb.items() if not k.startswith('_')}


with st.sidebar:
    if st.button(f"Logout: {st.session_state.cm.cookies['userid']}", icon=':material/logout:', type='primary'):
        st.session_state.cm.delete('userid')
        loading("Logging out...")

    if st.button("User Guide"):
        st.session_state.display_user_guide = True
   
    chatversion = st.expander("Chatbot Version", expanded=False)
    chatversion.info(f"""**GenAI**: `{version}`   
    **Emb Model**: `text-embedding-3-large(dimension=1024)`   
    **LLM Model**: `{os.getenv("AZURE_OPENAI_MODEL", "N/A")}`  
    """)

    chatsettings = st.expander("Chatbot Settings", expanded=False)
    group = chatsettings.selectbox('Select Group', list(groupdb.keys()), index=None, help='Pick a group if you would like to automatically select a pre-defined list of spaces.')
    default_spaces = []
    if group:
        ### Get the intersection of groupdb[group] and faiss_dbs_keys
        default_spaces = set(groupdb[group]) & set(faiss_dbs_keys)
    spaces = chatsettings.multiselect('Select spaces', faiss_dbs_keys, default=default_spaces, help='Select the spaces you would like the chatbot to search info from. A space is a collection of documents that the chatbot can search from.')

    if chatsettings.button("Clear Chat"):
        st.session_state.messages = []

    if chatsettings.checkbox("Enable Chat History"):
        st.session_state.enable_chat_history = True
    else:
        st.session_state.enable_chat_history = False

    #st.session_state.responsemode = chatsettings.radio(f"Response Mode:", ["Direct", "CoT", "ToT"], help='Check "User Guide" for details.', index=0, horizontal=True)
    st.session_state.responsemode = "Direct"


    faissdbs = []
    for space in spaces:
        faissdbs.append(faiss_dbs[space]['dbpath'])
            
    with st.form("Feedback", clear_on_submit=True):
        feedback_thumb = st.feedback()
        feedback_text = st.text_input("Feedback Message (optional)")
        feedback_submitted = st.form_submit_button("Send Feedback")
        if feedback_submitted:
            ### Create <yyyy><mm> folder
            now = datetime.datetime.now()
            yyyymm = now.strftime("%Y%m")
            feedback_dir = os.path.join(rootdir, 'feedback', yyyymm)
            feedback_dir = f'/nfs/site/disks/da_scratch_1/users/yltan/genailogs/altera_sc/aichatbot_feedback/{yyyymm}'
            os.system(f"mkdir -p {feedback_dir}; chmod 777 {feedback_dir}")

            ### Write feedback to json file
            feedback_json = os.path.join(feedback_dir, f"{now.strftime('%Y%m%d%H%M%S')}.json")
            data = {
                "userid": st.session_state.cm.cookies['userid'],
                "version": version,
                "thumb": feedback_thumb,
                "feedback": feedback_text,
                "spaces": spaces,
                "faissdbs": faissdbs,
                "messages": st.session_state.messages
            }
            with open(feedback_json, 'w') as f:
                json.dump(data, f, indent=4)
                st.toast("Feedback submitted, Thank you!", icon=':material/cloud_upload:')
            os.system(f"chmod 777 {feedback_json}")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        ### To support /sp command, because /sp output is in dataframe format
        if message['role'] == 'assistant' and message['content'].startswith('+') and message['content'].endswith('+'):
            st.dataframe(convert_mysql_table_to_panda_dataframe(message['content']))
        else:
            st.markdown(message['content'])


# React to user input
if prompt := st.chat_input("What's up?", accept_file=True, file_type=['png', 'jpg', 'jpeg', 'txt', 'log', 'pdf']):

    attached_filetype = None    # txt, image
    attached_string = None
    if prompt['files']:
        if prompt['files'][0].name.endswith(('.png', '.jpg', '.jpeg')):
            imageIO = prompt['files'][0]
            st.image(imageIO)
            
            import base64
            attached_string = base64.b64encode(imageIO.getvalue()).decode('utf-8')
            attached_filetype = 'image'

        elif prompt['files'][0].name.endswith(('.txt', '.log')):
            textIO = prompt['files'][0]
            attached_string = textIO.getvalue().decode('utf-8')
            attached_filetype = 'txt'

        elif prompt['files'][0].name.endswith('.pdf'):
            pdfIO = prompt['files'][0]
            from pypdf import PdfReader
            reader = PdfReader(pdfIO)
            attached_string = "\n".join([page.extract_text() for page in reader.pages])
            attached_filetype = 'txt'

    prompt = prompt.text.strip()


    ### Support slash commands
    if prompt == '/clear':
        st.session_state.messages = []
        st.rerun()
    elif prompt == '/help':
        st.session_state.display_user_guide = True
        st.rerun()
    elif prompt == '/spaces':
        st.markdown(f"""Selected spaces: `{', '.join(spaces)}`""")
        st.stop()
    elif prompt == '/gkhelp':
        cmd = f'ask_gk.py --examples'
        exitcode, stdout = subprocess.getstatusoutput(cmd)
        st.markdown(f"""# Examples Of Supported GK Queries    
        {stdout}""")
        st.stop()
    elif prompt == '/ddvhelp':
        cmd = f'/nfs/site/disks/da_infra_1/users/wplim/depot/da/infra/genai/main/bin/ask_ddv.py --examples'
        exitcode, stdout = subprocess.getstatusoutput(cmd)
        st.markdown(f"""# Examples Of Supported DDV Queries    
        {stdout}""")
        st.stop()
    elif prompt == '/sphelp':
        cmd = f'ask_syncpoint.py --examples'
        exitcode, stdout = subprocess.getstatusoutput(cmd)
        st.markdown(f"""# Examples Of Supported Syncpoint Queries    
        {stdout}""")
        st.stop()
    elif prompt == '/userhelp':
        cmd = f'ask_userinfo.py --examples'
        exitcode, stdout = subprocess.getstatusoutput(cmd)
        st.markdown(f"""# Examples Of Supported User Info Queries
        {stdout}""")
        st.stop()

    ##########################################################################
    ### Check if user has access group to respective faissdbs
    ##########################################################################
    user_groups = get_user_groups(st.session_state.cm.cookies['userid'])
    for space in spaces:
        reqgroup = faiss_dbs[space]['acg']
        if reqgroup and reqgroup not in user_groups:
            st.error(f"You do not have group '{reqgroup}' to access space '{space}'.")
            st.stop()


    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)
    
    ### Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    a = ChatbotAgent()
    a.kwargs['keep_alive'] = -1
    if st.session_state.get('enable_chat_history', False):
        a.kwargs['messages'] = copy.deepcopy(st.session_state.messages)
    else:
        a.kwargs['messages'] =  [copy.deepcopy(st.session_state.messages)[-1]]

    if attached_filetype and attached_string:
        if attached_filetype == 'txt':
            a.kwargs['messages'].insert(-1, {"role": "user", "content": f"**User Attached File**:  \n{attached_string}"})
        elif attached_filetype == 'image':
            a.kwargs['messages'].insert(-1, {"role": "user", "content": [{"type": "image_url", "image_url":{ "url": f"data:image/png;base64,{attached_string}"}}]})

    a.faiss_dbs = faissdbs
    a.responsemode = st.session_state.responsemode
    if not a.faiss_dbs:
        a.systemprompt = ''
    
    def llm_generator():
        for chunk in res:
            #yield chunk['message']['content']
            yield chunk

    with st.spinner("Thinking ... "):
        if prompt.startswith('/gk '):
            cmd = """ask_gk.py --quiet --query {}""".format(gu.quotify(prompt[4:]))
            exitcode, full_response = subprocess.getstatusoutput(cmd)
            with st.chat_message("assistant"):
                st.markdown(full_response)
                st.logger.get_logger("").info(f'''Question[{st.session_state.cm.cookies['userid']}]: {prompt}\nAnswer: {full_response}''')
        elif prompt.startswith('/user '):
            cmd = """ask_userinfo.py --query {}""".format(gu.quotify(prompt[6:]))
            exitcode, full_response = subprocess.getstatusoutput(cmd)
            with st.chat_message("assistant"):
                st.markdown(full_response)
                st.logger.get_logger("").info(f'''Question[{st.session_state.cm.cookies['userid']}]: {prompt}\nAnswer: {full_response}''')
        elif prompt.startswith('/sp'):
            cmd = """ask_syncpoint.py --quiet --query {}""".format(gu.quotify(prompt[4:]))
            exitcode, full_response = subprocess.getstatusoutput(cmd)
            with st.chat_message("assistant"):
                st.dataframe(convert_mysql_table_to_panda_dataframe(full_response))
                st.logger.get_logger("").info(f'''Question[{st.session_state.cm.cookies['userid']}]: {prompt}\nAnswer: {full_response}''')
        elif prompt.startswith('/ddv '):
            cmd = """/nfs/site/disks/da_infra_1/users/wplim/depot/da/infra/genai/main/bin/ask_ddv.py --query {}""".format(gu.quotify(prompt[6:]))
            exitcode, full_response = subprocess.getstatusoutput(cmd)
            with st.chat_message("assistant"):
                st.markdown(full_response)
                st.logger.get_logger("").info(f'''Question[{st.session_state.cm.cookies['userid']}]: {prompt}\nAnswer: {full_response}''')
        else:
            res = a.run()
            with st.chat_message("assistant"):
                full_response = st.write_stream(llm_generator())
                st.logger.get_logger("").info(f'''Question[{st.session_state.cm.cookies['userid']}]: {prompt}\nAnswer: {full_response}''')
    st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.session_state.get('display_user_guide', False):
    st.session_state.display_user_guide = False
    st.markdown(f'''
    ## User Guide
    - **Chatbot**: This is a GenAI chatbot (https://go2.altera.com/aichatbot) by Altera DMAI Team.  
    - **User Guide**: Clicking the "User Guide" button will display this user guide.  
    - **Wiki**: https://go2.altera.com/aichatbot_wiki
    - **Chatbot Settings**:
        - **Spaces**: Select the spaces you would like the chatbot to search info from.   
        - **Groups**: If you select a group, the chatbot will automatically select the spaces that are defined in the group.  
        - **Clear Chat**: When Chat History is enabled, be sure to clear the chat history if you want to start a new topic of conversation. Asking a question with different topics from the previous conversation will confuse the chatbot, and result in hallucination. In short, if the chatbot is not making sense, clear the chat history. 
        - **Enable Chat History**: If enabled, the chatbot will remember the previous conversation. If disabled, the chatbot will only remember the current question.
    - **Regex Search**:
        - Chatbot does not understand non-english words (e.g. rules code, etc). If you are looking for a specific code, use the regex search feature.
            - To use regex search, enclose the word in triple-angle-brackets. e.g. `<<<rules>>>`
            - e.g: `"Explain what does <<<D34.EN.4>>> error code means?"`
    - **Shortcut Slash Commands**:
        - _GENERAL Commands_:
            - `/clear`: Clear the chat history.
            - `/help`: Show this user guide.
            - `/spaces`: Show the selected spaces.
        - _GateKeeper Commands_:
            - `/gkhelp`: Show examples of supported GateKeeper queries.
            - `/gk <query>`: Ask a question to the GateKeeper system. e.g. `/gk What is the latest model for bypass_reg?`
        - _Syncpoint Commands_:
            - `/sphelp`: Show examples of supported Syncpoint queries.
            - `/sp <query>`: Ask a question to the Syncpoint system. e.g. `/sp Show me all syncpoints created in the past 1 month.`
        - _User Info Commands_:
            - `/userhelp`: Show examples of supported User Info queries.
            - `/user <query>`: Ask a question to the User Info system. e.g. `/user get me email address of Joanne Low`
    - **Available Spaces**:
    ''')

    with st.expander("Available Spaces"):
        st.markdown(f"Total {len(faiss_dbs)} spaces available.")
        st.markdown("You can select the spaces you would like the chatbot to search info from in the sidebar.")
        import pandas as pd
        pdt = pd.DataFrame(faiss_dbs).T
        for key in ['dbpath', 'acg', 'croncmd', 'emails']:
            del pdt[key]

        # Create a dictionary to configurre the columns
        column_configuration = {
            pdt.columns[0]: st.column_config.Column(
                "Space Name",
                width= "medium",    #  "small", "medium", "large", or a specific number in pixels
            )
        }

        # Display Dataframe with column configuration
        # st.dataframe(pdt, column_config=column_configuration)
        st.dataframe(pdt)
        #st.table(pdt)



def img_to_html(imgfile):
    import base64
    with open(imgfile, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    img_html = "<img src='data:image/png;base64,{}' />".format(encoded_string)
    return img_html


with st.chat_message("assistant"):
    st.markdown(f"""

    LLM Model: `{os.getenv("AZURE_OPENAI_MODEL", "N/A")}`  

    {img_to_html("/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/rubbish/images/image_1.png")}

    ===============================

    {img_to_html("./aidash.png")}

    ==============================
    {img_to_html("/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/kmmas/images/image_7.emf")}
    {img_to_html("/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/faissdbs/kmmas/images/image_7.jpg")}

    hahahaha

""", unsafe_allow_html=True)
    
