#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''
Documentation:
    https://github.com/ollama/ollama/blob/main/docs/api.md

Usage:
    
    from lib.agents.image_to_text_agent import ImageToTextAgent
    a = ImageToTextAgent()
    a.imagepath = '/path/to/your/image.png'   # Set your image path here
    a.systemprompt = 'your custom system prompt'  # Optional: customize the system prompt

    res = a.run()
    print(res.message.content)
    
'''
import os
import sys
import logging
from pprint import pprint, pformat

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent



class PromptboostAgent(BaseAgent):
    def __init__(self):
        super().__init__()
     
        ### llm settings for this agent
        self.kwargs['stream'] = False
        self.kwargs['options']['num_ctx'] = 2048 
        self.kwargs['options']['temperature'] = 0.0
        self.kwargs['options']['top_p'] = 0.0
       
        self.systemprompt = f'''
You are a Prompt Optimization Assistant.  
Your job is to take a user's raw prompt and rewrite it so that it becomes clear, specific, and maximally effective when used with a large language model (LLM).  
You should enhance the prompt by adding relevant context, clarifying ambiguous terms, and specifying the desired format of the response.
You should not change the fundamental intent of the user's prompt, but rather improve its clarity and effectiveness.
You should also ensure that the prompt is concise and free of unnecessary jargon or complexity.
You should output only the optimized prompt, without any additional commentary or explanation.
'''
    
    def run(self):
        kwargs = self.kwargs.copy()
       
        original_prompt = kwargs['messages'][-1]['content']
        self.kwargs['messages'] = [
            {"role": "system", "content": self.systemprompt},
            {"role": "user", "content": original_prompt},
        ]
        res = super().run()
        return res


if __name__ == '__main__':
    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    level = logging.INFO
    if '--debug' in sys.argv:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    a = PromptboostAgent()
    a.kwargs['messages'] = [{"role": "user", "content": sys.argv[1]}]
    res = a.run()
    print(res.message.content)
    

