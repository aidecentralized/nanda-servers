from mcp.server.fastmcp import FastMCP

from typing import Dict, List, Optional
import asyncio
import logging
import re
from urllib.parse import urlparse
from tenacity import retry, stop_after_attempt, wait_exponential
import docker
import mcp.types as types
import os

logger = logging.getLogger(__name__)

class MCPToolManager:
    def __init__(self, name: str):
        self.mcp = FastMCP(name)
        self._register_tools()

    def _register_tools(self):


        @self.mcp._mcp_server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """
            List available tools.
            Each tool specifies its arguments using JSON Schema validation.
            """
            return [
                types.Tool(
                    name="convert-contents",
                    description=(
                        "Converts files from latex to pdf. Transforms input content from any supported format "
                        "into the specified output format.\n\n"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contents": {
                                "type": "string",
                                "description": "The content to be converted (required if input_file not provided)"
                            },
                            "input_file": {
                                "type": "string",
                                "description": "Complete path to input file including filename and extension (e.g., '/path/to/input.md')"
                            },
                            "input_format": {
                                "type": "string",
                                "description": "Source format of the content (defaults to latex)",
                                "default": "latex",
                                "enum": ["markdown", "html", "pdf", "docx", "rst", "latex", "epub", "txt"]
                            },
                            "output_format": {
                                "type": "string",
                                "description": "Desired output format (defaults to pdf)",
                                "default": "pdf",
                                "enum": ["markdown", "html", "pdf", "docx", "rst", "latex", "epub", "txt"]
                            },
                            "output_file": {
                                "type": "string",
                                "description": "Complete path where to save the output including filename and extension (required for pdf, docx, rst, latex, epub formats)"
                            }
                        },
                        "oneOf": [
                            {"required": ["contents"]},
                            {"required": ["input_file"]}
                        ],
                        "allOf": [
                            {
                                "if": {
                                    "properties": {
                                        "output_format": {
                                            "enum": ["pdf", "docx", "rst", "latex", "epub", "markdown"]
                                        }
                                    }
                                },
                                "then": {
                                    "required": ["output_file"]
                                }
                            }
                        ]
                    },
                )
            ]

        @self.mcp._mcp_server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:    
            """
            Handle tool execution requests.
            Tools can modify server state and notify clients of changes.
            """
            if name not in ["convert-contents"]:
                raise ValueError(f"Unknown tool: {name}")
            
            #print(arguments)

            if not arguments:
                raise ValueError("Missing arguments")

            # Extract all possible arguments
            contents = arguments.get("contents")
            input_file = arguments.get("input_file")
            output_file = arguments.get("output_file")
            output_format = arguments.get("output_format", "pdf").lower()
            input_format = arguments.get("input_format", "latex").lower()
            
            # Validate input parameters
            if not contents and not input_file:
                raise ValueError("Either 'contents' or 'input_file' must be provided")
            
            # Define supported formats
            SUPPORTED_FORMATS = {'html', 'markdown', 'pdf', 'docx', 'rst', 'latex', 'epub', 'txt'}
            if output_format not in SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported output format: '{output_format}'. Supported formats are: {', '.join(SUPPORTED_FORMATS)}")
            
            # Validate output_file requirement for advanced formats
            ADVANCED_FORMATS = {'pdf', 'docx', 'rst', 'latex', 'epub'}
            # if output_format in ADVANCED_FORMATS and not output_file:
            #     raise ValueError(f"output_file path is required for {output_format} format")
            
            try:
                # Prepare conversion arguments
                extra_args = []
                
                # Handle PDF-specific conversion if needed

                # Convert content using pypandoc
                if input_file:
                    if not os.path.exists(input_file):
                        raise ValueError(f"Input file not found: {input_file}")
                    
                    converted_output = self.convert_tex_to_pdf(input_file)
                    result_message = f"File successfully converted and saved to: {converted_output}"

                    #if output_file:
                        # Convert file to file
                        # converted_output = pypandoc.convert_file(
                        #     input_file,
                        #     output_format,
                        #     outputfile=output_file,
                        #     extra_args=extra_args
                        # ) 
                            # Construct the command to run in the container
                        
                        
                        # cconverted_output = os.system('python C:/Users/siddh/hack/mcplayground/test_dock_tex.py')
                        
                return [
                    types.TextContent(
                        type="text",
                        text=result_message
                    )
                ]

            except Exception as e:
                # Handle Pandoc conversion errors
                error_msg = f"Error converting {'file' if input_file else 'contents'} from {input_format} to {output_format}: {str(e)}"
                raise ValueError(error_msg)

    def convert_tex_to_pdf(self, tex_file_path: str) -> str:
        """ converts tex to pdf """
        # Initialize the Docker client
        client = docker.from_env()

        input_file = tex_file_path
        directory_name = os.path.dirname(input_file)
        output_directory = directory_name

        # Set up the volume mapping
        volumes = {
            output_directory: {
                'bind': '/workdir',
                'mode': 'rw'
            }
        }
        
        # Get the filename without the path
        file_name = os.path.basename(tex_file_path)
        
        # Construct the command to run in the container
        command = f"xelatex -interaction=batchmode /workdir/{file_name} > NUL"
        
        try:
            # Run the container with the specified image, command, and volumes
            container = client.containers.run(
                image="danteev/texlive",
                command=command,
                volumes=volumes,
                remove=True,  # Equivalent to --rm
                detach=True   # Run in the background
            )
            
            # Get the container logs but suppress them (equivalent to > NUL)
            container.wait()
            
            # Check if the PDF was created successfully
            pdf_file = os.path.splitext(tex_file_path)[0] + '.pdf'
            if os.path.exists(pdf_file):
                #print(f"Successfully converted {tex_file_path} to PDF.")
                return pdf_file
            else:
                #print(f"Conversion failed. Check logs for details.")
                return False
                
        except docker.errors.DockerException as e:
            #print(f"Docker error: {e}")
            return False
        except Exception as e:
            #print(f"Error: {e}")
            return False

    # if at all you need to register resources, do it so
    def _register_resources(self):
        @self.mcp.resource("greeting://{name}")
        def get_greeting(name: str) -> str:
            return f"Bonjour, {name}!"

    @property
    def server(self):
        return self.mcp._mcp_server