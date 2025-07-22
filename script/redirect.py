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

st.markdown("""We have moved!  
Kindly access the chatbot at [https://go2.altera.com/aichatbot](https://go2.altera.com/aichatbot) from now on.""")
