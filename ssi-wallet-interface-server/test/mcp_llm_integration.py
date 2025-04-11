import asyncio
import json
import re
import warnings
from datetime import datetime
from typing import Any, Dict, List, Union

import aiohttp
import pytest
import pytest_asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

# Suppress specific deprecation warnings (see cite_python_warnings_doc, cite_pydantic_doc)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.v1.typing")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="ollama._types")
warnings.filterwarnings("ignore", category=pytest.PytestDeprecationWarning)
warnings.filterwarnings("ignore", message="Accessing the 'model_fields' attribute on the instance is deprecated")

console = Console()


# -----------------------------------------------------------------------------
# Fixtures and Model Instances
# -----------------------------------------------------------------------------
@pytest.fixture
def persona() -> str:
    """
    Provide a helpful customer support assistant persona. You facilitate access to a users ID Agent tenancy in a Xanadu Traction Custodial Wallet Service. Remember that if you seee any tool output you see is there to help you answer the user's questions. It may just be that you need to relay the information form tool calls if you see them. Explain results as if to a completely non-technical person.
        """
    return (
        "You are a helpful customer support assistant, always greet the user politely. "
        "Explain everything like you are speaking to a 3 year old. "
        "You may have to perform multi-stage tasks to complete the user's requests."
    )


@pytest.fixture
def llama_model() -> ChatOllama:
    """
    Return an instance of ChatOllama using the llama model.
        """
    return ChatOllama(model="llama3.2:latest", temperature=0, top_p=1)


@pytest.fixture
def qwq_model() -> ChatOllama:
    """
    Return an instance of ChatOllama using the qwq model.
    
    See cite_langchain_ollama_doc.
    """
    return ChatOllama(model="qwq:latest", temperature=0, top_p=1)

@pytest.fixture
def mistral_model() -> ChatOllama:
    """
    Return an instance of ChatOllama using the qwq model.
    
    See cite_langchain_ollama_doc.
    """
    return ChatOllama(model="mistral-small3.1", temperature=0, top_p=1)


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
def convert_response(obj: Any) -> Any:
    """
    Recursively convert an object into a JSON-serializable structure.
    If an item is not directly serializable, use its text() method or fallback to str().
        """
    if isinstance(obj, list):
        return [convert_response(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_response(value) for key, value in obj.items()}
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return obj.text() if hasattr(obj, "text") else str(obj)


def print_tool_calls(tool_calls: List[Dict[str, Any]]) -> None:
    """
    Display tool calls in a formatted table using the Rich library.
    
    """
    table = Table(title="Tools Accessed")
    table.add_column("Step", style="cyan", no_wrap=True)
    table.add_column("Tool Name", style="magenta")
    table.add_column("Timestamp", style="green")
    table.add_column("Tool Output", style="yellow")
    
    for idx, call in enumerate(tool_calls, start=1):
        tool_name = str(call.get("tool_name", "N/A"))
        timestamp = str(call.get("timestamp", "N/A"))
        output = convert_response(call.get("tool_output", ""))
        table.add_row(f"Step {idx}", tool_name, timestamp, output)
    console.print(table)


def print_chain_graph(cag: List[Dict[str, Any]]) -> None:
    """
    Print the compute graph (chain-of-actions) as a tree using Rich.
    
    """
    tree = Tree("Compute Graph (Chain-of-Actions)")
    for idx, step in enumerate(cag, start=1):
        tool_name = str(step.get("tool_name", "N/A"))
        timestamp = str(step.get("timestamp", "N/A"))
        node = tree.add(f"[cyan]Step {idx}[/cyan] - [magenta]{tool_name}[/magenta] @ [green]{timestamp}[/green]")
        tool_out = convert_response(step.get("tool_output", ""))
        if tool_out:
            node.add(f"[yellow]Output:[/yellow] {tool_out}")
    console.print(tree)


# -----------------------------------------------------------------------------
# Main Agent Query Processor Function
# -----------------------------------------------------------------------------
async def process_query(query: str, agent: Any, persona: str = None) -> Dict[str, Any]:
    """
    Process a query by invoking the agent and displaying the raw response, 
    events, compute graph, and AI messages.


    Parameters:
        query (str): The human query to process.
        agent (Any): The AI agent to invoke (should support `ainvoke`).
        persona (str, optional): A persona system prompt to set context.
        
    Returns:
        A dictionary containing the agent's safe response.
    """
    current_time = datetime.now().strftime("%H:%M:%S")
    console.rule(f"[bold green]{current_time} - Query: {query}")
    console.print(f"[bold blue]Human Input:[/bold blue] {query}\n")
    
    messages: List[Dict[str, str]] = []
    if persona:
        messages.append({"role": "system", "content": persona})
    messages.append({"role": "user", "content": query})

    try:
        response = await agent.ainvoke({"messages": messages})
    except Exception as error:
        console.print(f"[red]Error invoking agent: {error}[/red]")
        return {}

    safe_response = convert_response(response)
    console.print("\n[bold underline]Raw Response:[/bold underline]")
    console.print_json(data=safe_response)

    # Print any available events from the agent.
    if "events" in safe_response:
        console.print("\n[bold underline]MCP Agent Events:[/bold underline]")
        for event in safe_response["events"]:
            console.print(f"[blue]{event}[/blue]")

    # Display the compute graph, if available.
    if "cag" in safe_response:
        console.print("\n[bold underline]Compute Graph (Chain-of-Actions):[/bold underline]")
        print_chain_graph(safe_response["cag"])

    # Display tool calls, falling back to extracting from messages.
    if "tool_calls" in safe_response:
        console.print("\n[bold underline]Tools Accessed:[/bold underline]")
        print_tool_calls(safe_response["tool_calls"])
    else:
        tool_msgs = [
            msg for msg in safe_response.get("messages", [])
            if isinstance(msg, dict) and msg.get("role") == "tool"
        ]
        if tool_msgs:
            console.print("\n[bold underline]Extracted Tool Calls from messages:[/bold underline]")
            print_tool_calls(tool_msgs)

    # Process and display AI messages.
    ai_messages = safe_response.get("messages", [])
    console.print("\n[bold blue]AI Output:[/bold blue]")
    assistant_count = 0
    for msg in ai_messages:
        # Distinguish between dict and plain string responses.
        if isinstance(msg, dict):
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
        else:
            content = msg.strip()
            if not content or (persona and content == persona.strip()) or content == query.strip():
                continue
            role = "assistant"

        # Detect valid JSON outputs and reclassify as a tool output if needed.
        content_stripped = content.strip()
        if ((content_stripped.startswith("{") and content_stripped.endswith("}")) or
            (content_stripped.startswith("[") and content_stripped.endswith("]"))):
            try:
                json.loads(content_stripped)
                role = "tool"
            except Exception:
                pass

        # Extract and display any internal <think> blocks then remove them.
        think_blocks = re.findall(r"<think>(.*?)</think>", content, flags=re.DOTALL)
        if think_blocks:
            for think_block in think_blocks:
                cleaned_think = think_block.strip()
                if cleaned_think:
                    console.print(
                        Panel.fit(
                            f"[italic dim]{cleaned_think}[/]",
                            title="🧠 Think", border_style=""
                        )
                    )
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        # Print the final message with appropriate formatting.
        if role == "tool":
            console.print(Panel.fit(content, title="🛠️ Tool Output", border_style="magenta"))
        elif content:
            assistant_count += 1
            console.print(
                Panel.fit(Text.from_markup(content), title=f"AI Message {assistant_count}", border_style="bright_blue")
            )

    return safe_response


# -----------------------------------------------------------------------------
# Asynchronous Tests using pytest and pytest_asyncio
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_tenant_status(llama_model: ChatOllama, persona: str) -> None:
    """
    Test to verify that a summary of tenant details can be retrieved.

    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llama_model, tools)
            question = "Could you please get me a summary of details about my tenant? \n"
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0


@pytest.mark.asyncio
async def test_list_connections(llama_model: ChatOllama, persona: str) -> None:
    """
    Test to verify that active connections are listed.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llama_model, tools)
            question = "Could you please query my active connections?\n"
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0


@pytest.mark.asyncio
async def test_oob_invitation(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of an out-of-band SSI agent invitation.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = "Could you create an out of band SSI agent invitation for my friend Bob? I'd like their alias to be Bob. Give me the url \n"
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0


@pytest.mark.asyncio
async def test_scheme_creation(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "I'd like to create a new scheme named after NANDA"
                "The scheme version is '4.0' and "
                "the exact attribute name that I want is 'hackathon_attendance'. \n"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0

@pytest.mark.asyncio
async def test_list_schemes(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "Which Schemes have I created? \n"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0


@pytest.mark.asyncio
async def test_credential_creation(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA credential scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "I'd like to create one single new credential defnition using the scheme the fourth version of the NANDA scheme."
                "The credential definition tag should be 'NANDA TOP CREDENTIAL'. The credential definition should support revocation. "
                "If the credential definition already exists then that's fine, mission accomplished. \n"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0


@pytest.mark.asyncio
async def test_list_credentials(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "Which credential definitions have I already created?\n"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0



@pytest.mark.asyncio
async def test_send_message(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "Please send a message to my active connection Bob? Say 'Hi Bob'"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0

@pytest.mark.asyncio
async def test_receive_message(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "Please check for messages. Let me know who it was and what they said!"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0          


# @pytest.mark.asyncio
async def test_credential_offer(mistral_model: ChatOllama, persona: str) -> None:
    """
    Test to verify the creation of a new NANDA scheme.
    
    """
    server_params = StdioServerParameters(command="python", args=["../tools/traction_api.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(mistral_model, tools)
            question = (
                "I'd like you to send a credential offer to my connection 'Bob'. I'd like to send them one of the 'NANDA TOP CREDENTIAL' credentials, mark them as having attended.\n"
            )
            response = await process_query(query=question, agent=agent, persona=persona)
            assert isinstance(response, dict)
            assert "messages" in response
            assert len(response["messages"]) > 0  




# -----------------------------------------------------------------------------
# Main Tool Server Entry-Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    from tools import start_tool_server
    start_tool_server()


    