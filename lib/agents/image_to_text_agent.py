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
import base64

rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, rootdir)
import lib.genai_utils as gu
from lib.agents.base_agent import BaseAgent



class ImageToTextAgent(BaseAgent):
    def __init__(self):
        super().__init__()
     
        self.token_limit = 2000

        ### llm settings for this agent
        self.kwargs['stream'] = False
        self.kwargs['options']['num_ctx'] = 11111
        self.kwargs['options']['temperature'] = 0.0
        self.kwargs['options']['top_p'] = 0.0
       
        self.imagepath = None
        
        self.systemprompt = '''
Describe this electrical engineering image. Focus on the following aspects:

Core Components: Identify and list the primary electrical and electronic components present. Include items such as circuit boards, microcontrollers, capacitors, resistors, diodes, transformers, power supplies, motors, generators, solar panels, batteries, cables, and connectors.

Context and Purpose: Explain the likely function or application of the components. Is it a schematic diagram, a printed circuit board (PCB) layout, a power grid infrastructure, a robotics system, or a solar energy setup? Describe its role within a larger system or project.

Visual Details: Note the physical arrangement and connections of the components. Is the image a close-up or a wide shot? Are there any specific markings, labels, or symbols visible on the parts or diagram? Mention the color, size, and material of significant elements.

The description should be clear, detailed, and not exceed 2000 tokens.
        '''

        self.systemprompt = '''
Describe this image related to the semiconductor industry. The description should be suitable for a vector database and should not exceed 2000 tokens. Focus on the following key aspects:

Core Components and Technology: Identify the primary elements in the image. This could include silicon wafers, integrated circuits (ICs), microchips, printed circuit boards (PCBs), transistors, diodes, resistors, or specific packaging types (e.g., QFN, BGA). Also, mention the fabrication process or technology node if discernible (e.g., CMOS, FinFET, 7nm, 5nm).

Visual Representation and Context: Specify the nature of the image. Is it a photograph of a physical component, a schematic diagram, a micrograph (e.g., SEM, TEM), a layout diagram (e.g., GDSII), a flowchart of a process, or a block diagram of a system? Describe the scale (e.g., macro, micro, nanoscale) and the viewpoint (e.g., top-down, cross-section, close-up).

Function and Application: Explain the purpose of the depicted item or process. Is it a memory chip, a processor (CPU/GPU), a sensor, a power management IC, or a radio-frequency (RF) circuit? Describe its role within a larger system (e.g., mobile device, data center, automotive electronics).

Process and Manufacturing Details: If the image shows a manufacturing or R&D process, describe the stages or equipment involved. This could include wafer photolithography, etching, deposition, doping, dicing, or packaging. Note any visible cleanroom environment, tools, or machinery (e.g., steppers, etchers).

Data and Metadata: If there are any visible labels, part numbers, company logos, test points, or annotations, include them. These details are crucial for precise similarity searches.

The description should be clear, detailed, and directly related to the semiconductor and microelectronics domain."

        '''
    
    def get_base64_image(self, image_path):
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def run(self):
        kwargs = self.kwargs.copy()
        base64_image = self.get_base64_image(self.imagepath)
       
        a.kwargs['messages'] = [
            {"role": "user", "content": [{"type": "image_url", "image_url":{ "url": f"data:image/png;base64,{base64_image}"}}]},
            {"role": "user", "content": self.systemprompt}
        ]

        res = super().run()
        return res


if __name__ == '__main__':
    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    logging.basicConfig(level=logging.DEBUG)
    a = ImageToTextAgent()
    a.imagepath = sys.argv[1]
    res = a.run()
    print(res.message.content)
    

