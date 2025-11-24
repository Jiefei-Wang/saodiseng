from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple
from modules.FunctionTools import FunctionTools

with open("prompts/system_default.txt", 'r', encoding='utf-8') as f:
    _SYSTEM_PROMPT= f.read().strip()


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



class ToolAgent:
    """LLM agent wrapper that supports tools and optional batch chat.

    Parameters
    ----------
    client:
        An OpenAI-compatible client instance providing ``chat.completions.create``.
    model_name:
        Name of the chat model.
    function_tools:
        Optional ``FunctionTools`` instance (or plain tools list). If ``None``,
        no tools will be passed to the model.
    """

    def __init__(
        self,
        client: Any,
        model_name: str,
        tools: Optional[Any] = None,
        system_prompt: str = _SYSTEM_PROMPT,
        temperature: float = 0.7,
        max_repeat_tool_calls: int = 3,
    ) -> None:
        self._client = client
        self._model_name = model_name
        # 保存 FunctionTools 或 None；通过其 tools/call 使用
        if tools is None: 
            tools = FunctionTools()
        if isinstance(tools, list):
            tools = FunctionTools(functions=tools)
        self._function_tools = tools
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._max_repeat_tool_calls = max_repeat_tool_calls
    
    
    def _build_initial_messages(self, user_message: str, history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if history is None:
            return [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ]
        messages = history.copy()
        messages.append({"role": "user", "content": user_message})
        return messages

    def _complete_chat(self, messages: List[Dict[str, Any]], use_tools: bool = True) -> Any:
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,  # type: ignore[arg-type]
            tools=self._function_tools.tools if use_tools else None,
            tool_choice="auto" if use_tools and self._function_tools.tools else None,
            temperature=self._temperature,
        )
        
        return response

    def _run_chat_loop(
        self,
        messages: List[Dict[str, Any]],
        verbose: bool = False,
        use_tools: bool = True,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        response = self._complete_chat(messages, use_tools=use_tools)
        call_name_history = []
        current_repeat_count = 0
        while response.choices[0].finish_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                break

            if verbose:
                print(f"\nAgent decided to call {len(tool_calls)} function(s):")

            assistant_message: Dict[str, Any] = {
                "role": "assistant",
                "content": strip_think_tags(response.choices[0].message.content or ""),
            }
            assistant_message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,  # type: ignore[attr-defined]
                        "arguments": tc.function.arguments,  # type: ignore[attr-defined]
                    },
                }
                for tc in tool_calls
            ]
            messages.append(assistant_message)

            for tc in tool_calls:
                call_name = tc.function.name + ":" +str(tc.function.arguments)  # type: ignore[attr-defined]
                repeat_count = call_name_history.count(call_name)
                if repeat_count > current_repeat_count:
                    current_repeat_count = repeat_count
                    if current_repeat_count < self._max_repeat_tool_calls:
                        result = "Error: Detected repeated function call. Function calls aborted to prevent infinite loop."
                    else:
                        result = "Error: Maximum repeated function call limit reached. You cannot call any function anymore. Please provide your final answer."
                        use_tools = False
                else:
                    call_name_history.append(call_name)
                    
                    
                    function_name = tc.function.name  # type: ignore[attr-defined]
                    function_args = json.loads(tc.function.arguments)  # type: ignore[attr-defined]
                    if verbose:
                        print(f"  - Calling {function_name}({function_args})")
                    result = self._function_tools.call(function_name, function_args)
                    if verbose:
                        short = result[:100] + "..." if len(result) > 100 else result
                        print(f"    Result: {short}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

            response = self._complete_chat(messages, use_tools=use_tools)
            
        final_response = response.choices[0].message.content or "No response generated."
        final_response = strip_think_tags(final_response)
        messages.append({"role": "assistant", "content": final_response})
        return final_response, messages

    def chat(
        self,
        message: str,
        verbose: bool = False,
        history: Optional[List[Dict[str, Any]]] = None,
        use_tools: bool = True,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Single-turn chat with optional history and automatic tool handling."""
        messages = self._build_initial_messages(message, history)
        if verbose:
            print(f"\n{'='*60}")
            print(f"User Message: {message}")
            print(f"{'='*60}")
        reply, updated = self._run_chat_loop(messages, verbose=verbose, use_tools=use_tools)
        if verbose:
            print(f"\n{'='*60}")
            print(f"Agent Response:\n{reply}")
            print(f"{'='*60}\n")
        return reply, updated

    def batch_chat(
        self,
        messages_list: Sequence[str],
         histories: Optional[Sequence[Optional[List[Dict[str, Any]]]]] = None,
        verbose: bool = False,
        use_tools: bool = True,
    ) -> Tuple[List[str], List[List[Dict[str, Any]]]]:
        """Batch chat API using OpenAI batch endpoint semantics.

        当前实现为顺序调用逐条 ``chat``，保留接口形式以便后续
        替换为真正的批量 API。
        """
        if histories is None:
            histories = [None] * len(messages_list)
        results: List[str] = []
        all_histories: List[List[Dict[str, Any]]] = []
        for msg, hist in zip(messages_list, histories):
            reply, updated = self.chat(msg, verbose=verbose, history=hist, use_tools=use_tools)
            results.append(reply)
            all_histories.append(updated)
        return results, all_histories

