
import os
import json
from typing import Any, Optional, Union
from pathlib import Path


# Load system prompt
def _load_system_prompt() -> str:
    """Load the system prompt from prompts/system_default.txt"""
    prompt_path = "prompts/system_default.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "You are Table Expert, a helpful database assistant that helps users explore and understand database table structures."


def strip_think_tags(response: str) -> str:
    """
    Strip <think> and </think> tags from response.
    Safely handles cases where the tags don't exist.
    
    Args:
        response: The response text that may contain think tags.
    
    Returns:
        str: The response with think tags removed. If no think tags exist, returns original response.
    """
    if not response:
        return response
    
    # Check if both opening and closing tags exist
    if "<think>" not in response and "</think>" not in response:
        return response
    
    # Split by </think> tag
    parts = response.split("</think>")
    
    if len(parts) == 1:
        # No </think> found, return original
        return response
    
    # Get the part after </think>
    content_after_think = parts[1]
    
    # If there are multiple </think> tags, rejoin everything after the first one
    if len(parts) > 2:
        content_after_think = "</think>".join(parts[1:])
    
    # Strip leading/trailing whitespace
    return content_after_think.strip()


SYSTEM_PROMPT = _load_system_prompt()


# Define tools/functions for the agent
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search on the website using SerpAPI",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Search keyword"
                    }
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_web",
            "description": "Get the content of a web page given its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page to browse."
                    }
                },
                "required": ["url"]
            }
        }
    },
]
TOOLS=[]


def execute_function(function_name: str, function_args: dict) -> str:
    """
    Execute a database function with the given arguments.
    
    Args:
        function_name: The name of the function to execute.
        function_args: The arguments to pass to the function.
    
    Returns:
        str: The result of the function call.
    """
    # if function_name == "tbl_numbers":
    #     return tbl_numbers()
    # elif function_name == "list_tbls":
    #     return list_tbls(function_args.get("start", 0), function_args.get("end", 10))
    
    # else:
    return f"Unknown function: {function_name}"


def query_agent(user_question: str, verbose: bool = False, history: Optional[list] = None) -> tuple[str, list]:
    """
    Process a user question using the LLM agent.
    
    The agent will:
    1. Understand the user's question
    2. Decide which functions to call
    3. Execute the functions and gather information
    4. Return a comprehensive answer and updated history
    
    Args:
        user_question: The question from the user about the database.
        verbose: If True, print intermediate steps.
        history: Optional list of previous messages. If None, starts fresh conversation.
    
    Returns:
        tuple: (final_response, updated_history) - The agent's response and conversation history.
    """
    if history is None:
        # Start fresh conversation with system prompt
        messages: list = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_question
            }
        ]
    else:
        # Continue existing conversation
        messages = history.copy()
        messages.append({
            "role": "user",
            "content": user_question
        })
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"User Question: {user_question}")
        print(f"{'='*60}")
    
    # Initial API call
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,  # type: ignore
        tools=TOOLS,  # type: ignore
        tool_choice="auto",
        temperature=0.7
    )
    
    # Process tool calls in a loop
    while response.choices[0].finish_reason == "tool_calls":
        # Extract tool calls from the response
        tool_calls = response.choices[0].message.tool_calls
        
        if tool_calls is None:
            break
        
        if verbose:
            print(f"\nAgent decided to call {len(tool_calls)} function(s):")
        
        # Add assistant response to messages (strip think tags from all LLM responses)
        assistant_message: dict = {
            "role": "assistant",
            "content": strip_think_tags(response.choices[0].message.content or ""),
        }
        
        # Only add tool_calls if they exist
        if tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,  # type: ignore
                        "arguments": tool_call.function.arguments  # type: ignore
                    }
                }
                for tool_call in tool_calls
            ]
        
        messages.append(assistant_message)
        
        # Execute each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name  # type: ignore
            function_args = json.loads(tool_call.function.arguments)  # type: ignore
            
            if verbose:
                print(f"  - Calling {function_name}({function_args})")
            
            result = execute_function(function_name, function_args)
            
            if verbose:
                print(f"    Result: {result[:100]}..." if len(result) > 100 else f"    Result: {result}")
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
        
        # Make another API call with the tool results
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,  # type: ignore
            tools=TOOLS,  # type: ignore
            tool_choice="auto",
            temperature=0.7
        )
    
    # Extract final response (handles both tool call responses and direct responses)
    final_response = response.choices[0].message.content or "No response generated."
    
    # Strip think tags from final response
    final_response = strip_think_tags(final_response)
    
    # Add final assistant response to messages for history
    messages.append({
        "role": "assistant",
        "content": final_response
    })
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Agent Response:\n{final_response}")
        print(f"{'='*60}\n")
    
    return final_response, messages
