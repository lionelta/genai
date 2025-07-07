#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md
'''
import os
import sys
import ollama
from pprint import pprint

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
from lib.agents.base_agent import BaseAgent
import genai_utils as gu

class PickdbAgent(BaseAgent):

    def __init__(self):
        super().__init__()

        self.systemprompt = """
# Instruction  
Based on the given VECTOR DATABASE INFO, and a given QUESTION, decide which are the database which we should be using. Just answer the question in a json array format.

# Example

**VECTOR DATABASE INFO**  
fe_static_checks : DB which contains the content for FE RTL verification flows (VCS, Xcelium, Questa, Riviera, Veloce, Lint, CDC, DFT, VCLP)  
arc_faq : DB which contains the content for ARC FAQ  
altera_fe_faq : N/A  
icm_faq : DB which contains the content for ICM FAQ  


**question:** How to submit a job to ARC and ICM?  
**answer:** ["arc_faq", "icm_faq"]  

**question:** How to resolve xxxxxxx error?  
**answer:** []  

"""

        self.kwargs['stream'] = False
        self.kwargs['options']['top_p'] = 0.0
        self.kwargs['options']['temperature'] = 0.0
        


    def get_faissdbs_info_string(self):
        rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        faissdbs = gu.get_faiss_dbs(rootdir)
        txt = ''
        for dbname in faissdbs:
            txt += f"{dbname} : {faissdbs[dbname]['description']}  \n"
        return txt


    def run(self):
        """ Override default run() , because we need to insert db info and question into the chat """
        faissdb_info = self.get_faissdbs_info_string()
        self.kwargs['messages'][-1]['content'] = f"""
**VECTOR DATABASE INFO**  
{faissdb_info}  

**question:** {self.kwargs['messages'][-1]['content']}
"""
        return super().run()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    a = PickdbAgent()
    a.kwargs['messages'] = [
        {'role': 'user', 'content': sys.argv[1]}
    ]
    res = a.run()
    pprint(res)
    print('===========')
    print(res.message.content)
