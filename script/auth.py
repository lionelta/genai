#!/usr/intel/pkgs/python3/3.11.1/bin/python3
import os
import streamlit as st
import extra_streamlit_components as stx
import time
import requests
import json
import pwd
import grp

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
        st.write("Yoohoo !!!!:(")
        st.session_state.cm.set('userid', resjson['idsid'])
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


if 'userid' in st.session_state.cm.cookies:
    st.write(f"Welcome back {st.session_state.cm.cookies['userid']}!")
    st.write(f"User Groups: {get_user_groups(st.session_state.cm.cookies['userid'])}")
    if st.button("Logout"):
        st.session_state.cm.delete('userid')
        loading("Logging out...")
else:
    userid = st.text_input("Enter your user id")
    password = st.text_input("Enter your password", type="password")
    #password = st.text_input("Enter your password")
    authenticate(userid, password)
    

#st.info(f"Session count: {st.session_state.count}")
#st.write(st.session_state.cm.cookies)
#st.write(st.session_state)
st.write("--------------------- Footer ---------------------")

