#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
USAGE:
    import lib.agents.sentence_similarity_agent
    a = lib.agents.sentence_similarity_agent.SentenceSimilarityAgent()
    a.sentence_1 = 'she possesses a remarkable talent for playing the piano'
    a.sentence_2 = 'she is incredibly gifted at playing the piano'
    res = a.run()
    print(res.message.content)
'''
import os
import sys
import ollama
from pprint import pprint

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
from lib.agents.base_agent import BaseAgent
import genai_utils as gu

class SentenceSimilarityAgent(BaseAgent):

    def __init__(self):
        super().__init__()

        self.systemprompt = """
# Instruction  
Given a scale from 0-10, where 0 is the least similar, and 10 is the most, generate the score which you think best represents the similar in meaning for these 2 sentence.
Provide the response in json string, with keys "reason" and "score", nothing else.

# Example  

**sentense 1:** we offer free shipping on any order.  
**sentence 2:** you don't need to pay for the delivery.  
**answer:** {"reason": "both sentences convey the idea that the customer does not have to bear the cost of transporting their purchase, with 'free shipping' and 'dont need to pay for the delivery' essentially meaning the same thing in this context.", "score": 9}    

"""

        self.kwargs['stream'] = False
        self.kwargs['options']['top_p'] = 0.0
        self.kwargs['options']['temperature'] = 0.0

        self.sentence_1 = ''    # shuold be provided by the caller
        self.sentence_2 = ''    # shuold be provided by the caller


    def run(self):
        self.kwargs['messages'] = [
            {'role': 'user', 'content': f'''  
**sentense 1:** {self.sentence_1}  
**sentence 2:** {self.sentence_2}  
'''}]
        return super().run()


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    a = SentenceSimilarityAgent()
    pairs = [
        [
            'she possesses a remarkable talent for playing the piano',
            'she is incredibly gifted at playing the piano'
        ],
        [
            'the room was quite cold',
            'the room had a noticeable chill'
        ],
        [
            'the heavy rain poured down, soaking everything in the garden',
            'the plants were gently watered by the rain'
        ],
        [
            'the fluffy clouds drifted lazily across the bright blue sky',
            'the cloud service provide by the company is very reliable'
        ],
    ]
    for pair in pairs:
        a.sentence_1 = pair[0]
        a.sentence_2 = pair[1]
        res = a.run()
        print(f'''
sentence 1: {pair[0]}
sentence 2: {pair[1]}
{res.message.content}              
        ''')
        print('==================================')
