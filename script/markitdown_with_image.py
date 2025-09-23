#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.10.11_sles12_sscuda/bin/python


import os
import sys
import logging
import argparse
import os
from markitdown import MarkItDown
ROOTDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, ROOTDIR)
import lib.genai_utils
from lib.agents.base_agent import BaseAgent


def main():
    prompt = '''Describe this image related to the semiconductor industry. The description should be suitable for a vector database and should not exceed 2000 tokens. Focus on the following key aspects:

Core Components and Technology: Identify the primary elements in the image. This could include silicon wafers, integrated circuits (ICs), microchips, printed circuit boards (PCBs), transistors, diodes, resistors, or specific packaging types (e.g., QFN, BGA). Also, mention the fabrication process or technology node if discernible (e.g., CMOS, FinFET, 7nm, 5nm).

Visual Representation and Context: Specify the nature of the image. Is it a photograph of a physical component, a schematic diagram, a micrograph (e.g., SEM, TEM), a layout diagram (e.g., GDSII), a flowchart of a process, or a block diagram of a system? Describe the scale (e.g., macro, micro, nanoscale) and the viewpoint (e.g., top-down, cross-section, close-up).

Function and Application: Explain the purpose of the depicted item or process. Is it a memory chip, a processor (CPU/GPU), a sensor, a power management IC, or a radio-frequency (RF) circuit? Describe its role within a larger system (e.g., mobile device, data center, automotive electronics).

Process and Manufacturing Details: If the image shows a manufacturing or R&D process, describe the stages or equipment involved. This could include wafer photolithography, etching, deposition, doping, dicing, or packaging. Note any visible cleanroom environment, tools, or machinery (e.g., steppers, etchers).

Data and Metadata: If there are any visible labels, part numbers, company logos, test points, or annotations, include them. These details are crucial for precise similarity searches.

The description should be clear, detailed, and directly related to the semiconductor and microelectronics domain.'''

    f = BaseAgent().chat_factory
    client = f.get_azure_openai_client()
    model = os.getenv("AZURE_OPENAI_MODEL", 'gpt-4.1-nano')
    md = MarkItDown(llm_client=client, llm_model=model)
    result = md.convert(sys.argv[1])
    print(result.text_content)


if __name__ == '__main__':
    os.environ['AZURE_OPENAI_API_KEY'] = 'show me the money'
    main()

