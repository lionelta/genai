#!/usr/bin/env python
'''
How To Run:
    - ssh: asccf06294100.sc.altera.com
    - venv: 3.10.11_sles12_sscuda
    - proxyon
    - streamlit run --server.headless true --logger.level debug stream.py
'''

import os
os.environ['OLLAMA_HOST'] = 'asccf06294100.sc.altera.com:11434'
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
import tempfile


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.chatbot_agent import ChatbotAgent 
import bin.extract 

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'


### LLM Settings
llm_settings = gu.load_default_settings()


menu_items = {
    'Get Help': 'https://altera-corp.atlassian.net/wiki/spaces/tdmaInfra/pages/146738594/250215+-+How+To+Generate+My+Own+FAISS+DB',
    'About': "This is a GenAI chatbot. If you would like to have your wikispace added to the chatbot, please contact yoke.liang.tan.lionel@altera.com"
}
st.set_page_config(page_title='Chatbot', layout='wide', menu_items=menu_items)
st.title('Ask Pdf')

version = os.path.basename(rootdir)



with st.sidebar:
   
    chatversion = st.expander("Chatbot Version", expanded=False)
    chatversion.info(f"""**GenAI**: `{version}`   
    **Emb Model**: `{llm_settings['emb_model']}`   
    **LLM Model**: `{llm_settings['llm_model']}`  
    **Temperature**: `{llm_settings['temperature']}`  
    **Top P**: `{llm_settings['top_p']}`
    """)


    if st.button("Clear Chat"):
        st.session_state.messages = []

    if 'pdffile' not in st.session_state:
        st.session_state.pdffile = None
    pdffile = st.text_input("pdf file")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


# React to user input
if prompt := st.chat_input("What's up?"):
    # Display user message in chat message container
    with st.chat_message('user'):
        st.markdown(prompt)
    
    ### Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    a = ChatbotAgent()
    a.kwargs['keep_alive'] = -1
    a.kwargs['messages'] = copy.deepcopy(st.session_state.messages)
    a.systemprompt = ''
   
    def llm_generator(res):
        for chunk in res:
            yield chunk['message']['content']

    with st.spinner("Thinking ... "):
        if st.session_state.pdffile != pdffile:
            st.session_state.pdffile = pdffile
            
            ### generate faissdb
            st.session_state.faissdbpath = tempfile.mkdtemp()
            args = argparse.ArgumentParser().parse_args([])
            args.pdf = pdffile
            args.chunksize = 0
            args.chunkoverlap = 0
            args.method = 'none'
            args.wikispace = None
            args.pageids = None
            args.txtdir = None
            args.debug = True
            args.save = st.session_state.faissdbpath
            args.emb_model = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/pretrained_models/BAAI/bge-m3'
            args.disable_faissdb = False
            args.disable_regexdb = True
            bin.extract.main(args)

        a.faiss_dbs = [st.session_state.faissdbpath]
        res = a.run()
        with st.chat_message("assistant"):
            full_response = st.write_stream(llm_generator(res))
            st.logger.get_logger("").info(f'''Question: {prompt}\nAnswer: {full_response}''')
    st.session_state.messages.append({"role": "assistant", "content": full_response})



