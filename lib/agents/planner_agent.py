#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python
'''

======================================
## How to use ToolAgent
======================================
1.  Create a toolfile.py file that contains the functions you want to call.
2.  Set the toolfile attribute of the ToolAgent instance to the path of your toolfile.py file.
3.  Call the run() method of the ToolAgent instance to get the response.
4.  The response will be a list of return values from the functions called in the toolfile.py file.
    

======================================
## Code Example (ToolAgent):
======================================
    a = ToolAgent()
    a.toolfile = <path to toolfile.py>
    a.kwargs['messages'] = [{'role': 'user', 'content': <user query>}]
    response = a.run() 
    # Response(model='llama3.3' 
        created_at='2025-04-18T06:20:17.14553645Z' 
        done=True 
        done_reason='stop' 
        total_duration=12785807414 
        load_duration=8128787086 
        prompt_eval_count=917 
        prompt_eval_duration=2165000000 
        eval_count=34 
        eval_duration=1794000000 
        message=Message(role='assistant', 
            content='[
                {"function": "explain_code", "parameters": {"filelist": ["bin/ask.py"], "level": "high"}, "missing_params": []}
            ]', 
            images=None, 
            tool_calls=None
        )
    )
    
    # What you are interested should be only this: response.message['content']
    # You can now do whatever you want with the response. But if you would like to call the function in the toolfile.py, you can do it like this:
    outputs = a.execute_response(response)

    # outputs == [
        'stdout from function1',
        'stdout from function2',
        ... ... ...
    ]

    # If there is a missing parameter, the output will be:
    # outputs == [
        'missing_params: ["filelist"]',
        'stdout from function2',
        ... ... ...
    ]

======================================
## Toolfile.py Example:
======================================
    explain_code_dict = {
        'type': 'function',
        'function': {
            'name': 'explain_code',
            'description': 'explain the code of a given list of files, based on the given level.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'filelist': {
                        'type': 'list',
                        'description': 'The list of files to be explained',
                        'required': True,
                    },
                    'level': {
                        'type': 'string',
                        'description': 'The level of detail for the explanation, whereby high is the least detailed, mid is the medium detailed, and low is the most detailed.',
                        'choices': ['high', 'mid', 'low'],
                        'default': 'high',
                        'required': False,
                    }
                },
            },
        }
    }
    def explain_code(filelist='', level='high'):
        exe = os.path.join(rootdir, 'bin', 'explain_code.py')
        cmd = '{} -f {} -e {}'.format(exe, ' '.join(filelist), level)
        LOGGER.debug(f'Tool Ran: {cmd}')
        os.system(cmd)
    # --------------------------------------------------
    other_tool_dict = {
        'type': 'function',
        'function': {
            'name': 'other_tool',
            ...   ...   ...
    }       
    def other_tool():
        ... ... ...
    # --------------------------------------------------
    all_tools = [explain_code_dict, other_tool_dict]


======================================
## Real Examples:
======================================
ToolAgent usage: 
    bin/myhelper.py

toolfile.py:
    toolfiles/myhelper_toolfile.py


'''
import os
import sys
import ollama
from pprint import pprint
import importlib
import json

rootdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, rootdir)
from agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__()

        self.systemprompt = ''

        ### Overriding default settings
        self.kwargs['stream'] = False
        self.kwargs['options']['top_p'] = 0.0
        self.kwargs['options']['temperature'] = 0.0

        self.toolfile = None


    def run(self):
        self.mytools = self.load_toolfile()
        self.systemprompt = """

You are an intelligent Planner Agent responsible for designing and orchestrating a sequence of prompts to achieve a complex user goal. Your goal is to break down the user's request into smaller, manageable steps, and then formulate individual prompts for other specialized agents (e.g., a Research Agent, a Content Generation Agent, a Code Generation Agent). You have the ability to chain these prompts together, using the output of one agent as the input for the next, to progressively achieve the final objective.

**User Goal:** [Clearly state the user's ultimate goal here. Be as specific as possible.]

**Your Thinking Process:**

1.  **Deconstruct the Goal:** Analyze the user's goal and identify the core components and sub-tasks required to fulfill it. What are the natural stages or phases involved?
2.  **Identify Necessary Agents:** Determine which specialized agents are best suited for each sub-task. Consider their capabilities and the type of information or output they can provide.
3.  **Plan the Prompt Chain:** Design a logical sequence of prompts, ensuring that the output of each step provides valuable input for the subsequent step. Think about dependencies between tasks.
4.  **Formulate Individual Prompts:** For each step in the chain, create a clear and concise prompt for the designated agent. Ensure the prompt specifies:
    * **The Role of the Agent:** Clearly define the agent's persona and expertise for this specific task.
    * **The Specific Task:** What exactly should the agent do? Be precise and actionable.
    * **Input Data:** Specify any relevant information or context the agent needs (this might be the output from a previous agent).
    * **Desired Output Format:** How should the agent present its results? (e.g., a list, a paragraph, JSON format).
    * **Constraints and Guidelines:** Are there any specific rules or limitations the agent should adhere to?
5.  **Consider Potential Issues and Refinements:** Anticipate potential roadblocks or ambiguities in the plan. How can the prompt chain be designed to handle errors or unexpected outputs? Are there any iterative steps that might be beneficial?

**Output Format:**

Present your plan as a numbered list of steps, where each step includes:

1.  **Step Number:**
2.  **Agent:** [Name of the specialized agent]
3.  **Prompt for the Agent:** "[The exact prompt you would send to this agent]"
4.  **Expected Output:** [A brief description of what you expect this agent to produce]
5.  **How the Output Will Be Used:** [Explain how the output of this step will contribute to the overall goal and/or be used as input for the next step.]

**Example:**

Let's say the **User Goal** is: "Create a blog post comparing the benefits and drawbacks of two different programming languages (Python and JavaScript) for web development, including code examples for a simple task in each language."

Your plan might look like this:

1.  **Step Number:** 1
    **Agent:** Research Agent
    **Prompt for the Agent:** "Research and summarize the key benefits and drawbacks of using Python for web development. Focus on aspects like performance, ecosystem, learning curve, and common use cases."
    **Expected Output:** A concise summary of Python's pros and cons for web development.
    **How the Output Will Be Used:** This information will be used as content for the blog post.

2.  **Step Number:** 2
    **Agent:** Research Agent
    **Prompt for the Agent:** "Research and summarize the key benefits and drawbacks of using JavaScript for web development. Focus on aspects like performance, ecosystem, learning curve, and common use cases."
    **Expected Output:** A concise summary of JavaScript's pros and cons for web development.
    **How the Output Will Be Used:** This information will be used as content for the blog post.

3.  **Step Number:** 3
    **Agent:** Code Generation Agent
    **Prompt for the Agent:** "Provide a simple code example in Python that prints the message 'Hello from Python!' to the console."
    **Expected Output:** A short Python code snippet.
    **How the Output Will Be Used:** This will be included as a practical example in the blog post.

4.  **Step Number:** 4
    **Agent:** Code Generation Agent
    **Prompt for the Agent:** "Provide a simple code example in JavaScript that prints the message 'Hello from JavaScript!' to the console."
    **Expected Output:** A short JavaScript code snippet.
    **How the Output Will Be Used:** This will be included as a practical example in the blog post.

5.  **Step Number:** 5
    **Agent:** Content Generation Agent
    **Prompt for the Agent:** "Using the summaries of Python and JavaScript benefits/drawbacks (from steps 1 and 2) and the code examples (from steps 3 and 4), write a blog post comparing these two languages for web development. Structure the post with an introduction, separate sections for Python and JavaScript pros and cons, a section comparing the code examples, and a concluding summary."
    **Expected Output:** A complete blog post in markdown format.
    **How the Output Will Be Used:** This is the final output of the multi-agent workflow.

**Key Considerations for Intelligence:**

* **Dynamic Planning:** The planner should ideally be able to adjust its plan based on the output of previous agents. If an agent fails or produces unexpected results, the planner should be able to revise the subsequent prompts or even introduce new steps.
* **Dependency Awareness:** The planner needs to understand the dependencies between tasks. Some tasks might need to be completed before others can begin.
* **Resource Management:** In a more complex system, the planner might also need to consider which agents are available and allocate tasks accordingly.
* **Error Handling:** The planner should anticipate potential errors and include steps to handle them, such as asking an agent to revise its output or trying a different approach.
* **Goal Decomposition Heuristics:** Consider providing the planner with some high-level heuristics for breaking down common types of user goals (e.g., research, creative writing, problem-solving).
* **Access to Agent Capabilities:** The planner needs to "know" what each specialized agent is capable of. This could be through a description or a more formal interface.

"""








        """You are an intelligent planner for automation.
        Your task is to analyze user requests and determine the appropriate function(s) to execute. 
        You will search for matching functions based on the user's intent and available tools.

Your output must be in JSON array format, adhering to the following structure:

* **If a matching function is found (with parameters):**
    [{"function": "name_of_the_function", 
    "parameters": {"parameter1": "value1", "parameter2": "value2", ...},
    "missing_params": ["parameter3", "parameter4", ...]}]
    }]

* **If a matching function is found (without parameters):**
    [{"function": "name_of_the_function", "parameters": {}}, "missing_params": []}]

* **If multiple matching functions are found (with parameters):**
    [{"function": "name_of_the_function1", 
    "parameters": {"parameter1": "value1", "parameter2": "value2", ...},
    "missing_params": ["parameter3", "parameter4", ...]}, 
    {"function": "name_of_the_function2", 
    "parameters": {"parameter1": "value1", "parameter2": "value2", ...},
    "missing_params": ["parameter3", "parameter4", ...]},
    ...]   

* **If no matching function is found:**
    []

**Instructions:**

1.  **Understand the User Request:** Carefully analyze the user's input to determine their intent.
2.  **Function Matching:** Compare the user's intent with the available functions.
3.  **Parameter Extraction:** If a matching function is found, extract the necessary parameters from the user's input.
4.  **JSON Output:** Format your response strictly as a JSON array, following the specified structure. If there are multiple functions to call, include them in the array. Do not format the response using markdown or triple backticks. Return it as plain text. 
5.  **No Explanations:** Do not provide any additional explanations or conversational responses. Only return the JSON output.

**Available Functions:**
""" + json.dumps(self.mytools.all_tools)

        res = super().run()
        return res


    def execute_response(self, res):
        ''' res = response returned from self.run() 
        
        res.message: Message(role='assistant', 
        content='[{
            "function": "explain_code", 
            "parameters": {"filelist": ["./bin/ask.py", "./bin/explain_code.py", "./lib/agents/*.py"]}, 
            "missing_params": []
        }]'

        return = [return value from 1st function, return value from 2nd function, ...]
        '''
        retlist = []
        try:
            data = json.loads(res.message.content)
            for e in data:
                if e['missing_params']:
                    retlist.append('missing_params: {}'.format(e['missing_params']))
                    continue
                
                try:
                    retlist.append(getattr(self.mytools, e['function'])(**e['parameters']))
                except Exception as e:
                    retlist.append(str(e))
        except Exception as e:
            retlist.append(str(e))
    
        return retlist


    def load_toolfile(self):
        spec = importlib.util.spec_from_file_location("module.mytools", self.toolfile)
        mytools = importlib.util.module_from_spec(spec)
        sys.modules['module.mytools'] = mytools
        spec.loader.exec_module(mytools)
        return mytools


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    os.environ['OLLAMA_HOST'] = 'asccf06294100.sc.altera.com:11434'
    a = ToolAgent()
    a.toolfile = '/nfs/site/disks/da_scratch_1/users/yltan/depot/da/infra/genai/main/toolfile_example.py'
    a.kwargs['messages'] = [
        {'role': 'user', 'content': 'what are the tasks that you can do?'},
    ]
    res = a.run()

    pprint(res)
