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

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

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


menu_items = {
    'Get Help': 'https://altera-corp.atlassian.net/wiki/spaces/tdmaInfra/pages/146738594/250215+-+How+To+Generate+My+Own+FAISS+DB',
    'About': "This is a GenAI chatbot. If you would like to have your wikispace added to the chatbot, please contact yoke.liang.tan.lionel@altera.com"
}
st.set_page_config(page_title='Chatbot', layout='wide', menu_items=menu_items)
st.title('AI Chatbot - Alpha Version')

faiss_dbs = gu.get_faiss_dbs(rootdir)

### Move psgcth2tfm to first element
faiss_dbs_keys = []
for k in faiss_dbs:
    if k == 'psgcth2tfm':
        faiss_dbs_keys.insert(0, k)
    else:
        faiss_dbs_keys.append(k)

version = os.path.basename(rootdir)



with st.sidebar:
    if st.button("User Guide"):
        st.session_state.display_user_guide = True
   
    chatversion = st.expander("Chatbot Version", expanded=False)
    chatversion.info(f"""**GenAI**: `{version} (2lib)`   
    **Emb Model**: `{llm_settings['emb_model']}`   
    **LLM Model**: `{llm_settings['llm_model']}`  
    **Temperature**: `{llm_settings['temperature']}`  
    **Top P**: `{llm_settings['top_p']}`
    """)

    chatsettings = st.expander("Chatbot Settings", expanded=False)
    spaces = chatsettings.multiselect('Select spaces', faiss_dbs_keys, default = [])

    if chatsettings.button("Clear Chat"):
        st.session_state.messages = []

    if chatsettings.checkbox("Enable Chat History"):
        st.session_state.enable_chat_history = True
    else:
        st.session_state.enable_chat_history = False

    st.session_state.responsemode = chatsettings.radio(f"Response Mode:", ["Direct", "CoT", "ToT"], help='Check "User Guide" for details.', index=0, horizontal=True)


    faissdbs = []
    spaces = []
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

with st.expander(f"Loaded faissdbs:"):
    for db in faissdbs:
        st.write(db)

if "messages" not in st.session_state:
    st.session_state.messages = []


# React to user input
if prompt := st.chat_input("What's up?"):
    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)
   
    lib1 = open('2libfiles/1.lib', 'r').read()
    lib2 = open('2libfiles/2.lib', 'r').read()
    myquery = f'''you are an expert in synopsys liberty file. You are given 2 liberty files. Help the user with their query.   

    **Liberty File 1**: {lib1}  

    **Liberty File 2**: {lib2}  

    **User Query**: {prompt}  
    '''

    ### Add user message to chat history
    # disable chat history
    # st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages = [{"role": "user", "content": myquery}]

    a = ChatbotAgent()
    a.kwargs['keep_alive'] = -1
    if st.session_state.get('enable_chat_history', False):
        a.kwargs['messages'] = copy.deepcopy(st.session_state.messages)
    else:
        a.kwargs['messages'] =  [copy.deepcopy(st.session_state.messages)[-1]]

    a.kwargs['options']['num_ctx'] = 50000
    #a.kwargs['model'] = 'deepseek-r1:1.5b'

    a.faiss_dbs = faissdbs
    a.responsemode = st.session_state.responsemode
    if not a.faiss_dbs:
        a.systemprompt = ''
    
    def llm_generator():
        for chunk in res:
            yield chunk['message']['content']

    with st.spinner("Thinking ... "):
        res = a.run()
        with st.chat_message("assistant"):
            full_response = st.write_stream(llm_generator())
            st.logger.get_logger("").info(f'''Question: {prompt}\nAnswer: {full_response}''')
    st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.session_state.get('display_user_guide', False) or not st.session_state.get('messages', False):
    st.session_state.display_user_guide = False
    st.markdown(f'''
    ## User Guide
    - **Chatbot**: This is a 2lib chatbot  
    ''')


