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

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

menu_items = {
    'Get Help': 'https://go2.altera.com/aichatbot_wiki',
    'About': f"If you would like to have your wikispace added to the chatbot, please contact yoke.liang.lionel.tan@altera.com or joanne.low@altera.com",
    'Report a Bug': 'mailto:joanne.low@altera.com; yoke.liang.lionel.tan@altera.com'
}
st.set_page_config(page_title='Chatbot', layout='wide', menu_items=menu_items)
st.title('AI Chatbot - Alpha Version')

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
    **LLM Model**: `gpt-4o`  
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

    st.session_state.responsemode = chatsettings.radio(f"Response Mode:", ["Direct", "CoT", "ToT"], help='Check "User Guide" for details.', index=0, horizontal=True)


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
            os.system(f"mkdir -p {feedback_dir}")

            ### Write feedback to json file
            feedback_json = os.path.join(feedback_dir, f"{now.strftime('%Y%m%d%H%M%S')}.json")
            data = {
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


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


# React to user input
if prompt := st.chat_input("What's up?"):

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

    a.faiss_dbs = faissdbs
    a.responsemode = st.session_state.responsemode
    if not a.faiss_dbs:
        a.systemprompt = ''
    
    def llm_generator():
        for chunk in res:
            #yield chunk['message']['content']
            yield chunk

    with st.spinner("Thinking ... "):
        res = a.run()
        with st.chat_message("assistant"):
            full_response = st.write_stream(llm_generator())
            st.logger.get_logger("").info(f'''Question[{st.session_state.cm.cookies['userid']}]: {prompt}\nAnswer: {full_response}''')
    st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.session_state.get('display_user_guide', False) or not st.session_state.get('messages', False):
    st.session_state.display_user_guide = False
    st.markdown(f'''
    ## User Guide
    - **Chatbot**: This is a GenAI chatbot by Altera DMAI Team.   
    - **User Guide**: Clicking the "User Guide" button will display this user guide.  
    - **Feedback**: If you have any feedback, please use the feedback form. *(at the lower left corner)*
        - click the thumb-up(:material/thumb_up:) or thumb-down(:material/thumb_down:) icon
        - type your feedback message
        - click "Send Feedback"
    - **Chatbot Settings**:
        - **Spaces**: Select the spaces you would like the chatbot to search info from. If you are not sure, just select all. (*Selecting the accurate space(s) will help the chatbot to provide more accurate answers*)
        - **Clear Chat**: When Chat History is enabled, be sure to clear the chat history if you want to start a new topic of conversation. Asking a question with different topics from the previous conversation will confuse the chatbot, and result in hallucination. In short, if the chatbot is not making sense, clear the chat history. 
        - **Enable Chat History**: If enabled, the chatbot will remember the previous conversation. If disabled, the chatbot will only remember the current question.
        - **Response Mode**: 
            - **Direct**: This feature provides a direct answer to the query. 
            - **CoT(Chain Of Thought)**: This feature tries to reason thru the query step-by-step before providing a final answer. *(improve accuracy, slightly longer runtime)*
            - **ToT(Tree of Thought)**: This feature tries to reason thru the query thru 3 experts, step-by-step, before deciding on the best answer. *(improve accuracy, longer runtime)*  
    - **How To Ask (GOOD) Questions**:
        - **Avoid ambiguity**: Be clear and concise in your questions. Do not assume the Chatbot understands your context implicityly.
        - **Provide context**: If you are asking a question that requires context, provide the context.
        - **Regex Search**: Chatbot does not understand non-english words (e.g. rules code, etc). If you are looking for a specific code, use the regex search feature.
            - To use regex search, enclose the word in triple-angle-brackets. e.g. `<<<rules>>>`
            - e.g: `"Explain what does <<<D34.EN.4>>> error code means?"`
    - **Available Spaces**:
    ''')
    import pandas as pd
    pdt = pd.DataFrame(faiss_dbs).T
    for key in ['dbpath', 'acg', 'croncmd', 'emails']:
        del pdt[key]
    st.table(pdt)


