#!/nfs/site/disks/da_infra_1/users/yltan/venv/3.11.1_ipython/bin/python

import asyncio
import sys
import logging
import json
import os
import re

from pprint import pprint, pformat

from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import ollama

from dotenv import load_dotenv

load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
'''
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/mcp_client.log"),
        logging.StreamHandler()
    ]
)
'''

class MCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an SSE MCP server."""
        logger.debug(f"Connecting to SSE MCP server at {server_url}")

        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"Connected to SSE MCP Server at {server_url}. Available tools: {[tool.name for tool in tools]}")

    async def connect_to_stdio_server(self, server_script_path: str):
        """Connect to a stdio MCP server."""
        is_python = False
        is_javascript = False
        command = None
        args = [server_script_path]
        
        # Determine if the server is a file path or npm package
        if server_script_path.startswith("@") or "/" not in server_script_path:
            # Assume it's an npm package
            is_javascript = True
            command = "npx"
        else:
            # It's a file path
            is_python = server_script_path.endswith(".py")
            is_javascript = server_script_path.endswith(".js")
            if not (is_python or is_javascript):
                raise ValueError("Server script must be a .py, .js file or npm package.")
        
            command = "python" if is_python else "node"
            
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None
        )

        logger.debug(f"Connecting to stdio MCP server with command: {command} and args: {args}")

        # Start the server
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.writer = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.writer))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"Connected to stdio MCP Server. Available tools: {[tool.name for tool in tools]}")

    async def connect_to_server(self, server_path_or_url: str):
        """Connect to an MCP server (either stdio or SSE)."""
        # Check if the input is a URL (for SSE server)
        url_pattern = re.compile(r'^https?://')
        
        if url_pattern.match(server_path_or_url):
            # It's a URL, connect to SSE server
            await self.connect_to_sse_server(server_path_or_url)
        else:
            # It's a script path, connect to stdio server
            await self.connect_to_stdio_server(server_path_or_url)

    async def process_query(self, query: str, previous_messages: list = None) -> tuple[str, list]:
        """Process a query using the MCP server and available tools."""
        model = 'llama3.3'

        if not self.session:
            raise RuntimeError("Client session is not initialized.")
        
        messages = []
        """ ### Temporary disable chat history
        if previous_messages:
            messages.extend(previous_messages)
        """

        messages.append( 
            {
                "role": "user",
                "content": query
            }
        )
        
        response = await self.session.list_tools()
        ### Data structure of `response` output:-
        """
        ListToolsResult(
            meta=None,
            nextCursor=None,
            tools=[
                Tool(
                    name='add',
                    description='Add two numbers',
                    inputSchema={
                        'properties': {
                            'a': {'title': 'A', 'type': 'integer'},
                            'b': {'title': 'B', 'type': 'integer'}
                        },
                        'required': ['a', 'b'],
                        'title': 'addArguments',
                        'type': 'object'
                    },
                    annotations=None
                ),
                Tool(...),
                ... ... ...
            ]
        )
        """
        print(f'list_tools: {pformat(response)}')
        ### Convert tools to a format compatible with llama3.3 tools syntax
        available_tools = []
        for tool in response.tools:
            ### properties
            properties = dict()
            for prop in tool.inputSchema['properties']:
                properties[prop] = {
                    "type": tool.inputSchema['properties'][prop]['type'],
                    "description": tool.inputSchema['properties'][prop]['title']
                }
            available_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties
                    },
                    "required": tool.inputSchema['required'],
                }
            })

        # Initialize Claude API call
        logger.info(f"Sending query to {model}...")
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=available_tools,
            options={'num_ctx': 1000}
        )
        print(f"available_tools: {pformat(available_tools)}")
        print(f"response: {pformat(response)}")
        # Process response and handle tool calls
        final_text = []

        if response.message['tool_calls']:
            for tool in response.message['tool_calls']:
                tool_name = tool['function']['name']
                tool_args = tool['function']['arguments']

                # Execute tool call
                logger.debug(f"Calling tool {tool_name} with args {tool_args}...")
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool `{tool_name}` with args {tool_args}. Result: {result.content[0].text}]")
        return [final_text, messages]
    
    async def chat_loop(self):
        """Run an interactive chat loop with the server."""
        previous_messages = []
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == "quit":
                    break
                
                #  Check if the user wants to refresh conversation (history)
                if query.lower() == "refresh":
                    previous_messages = []
            
                response, previous_messages = await self.process_query(query, previous_messages=previous_messages)
                print("\nResponse:", response)
            except Exception as e:
                print("Error:", str(e))

    async def clenup(self):
        """Clean up resources."""
        await self.exit_stack.aclose()
        if hasattr(self, '_session_context') and self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, '_streams_context') and self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <server_script_path_or_url>")
        print("Examples:")
        print("  - stdio MCP server (npm): python client.py @playwright/mcp@latest")
        print("  - stdio MCP server (python): python client.py ./weather.py")
        print("  - SSE MCP server: python client.py http://localhost:3000/mcp")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.clenup()
        print("\nMCP Client Closed!")


if __name__ == "__main__":
    asyncio.run(main())



