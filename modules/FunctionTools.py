
from typing import Any, Dict, List
import inspect
import textwrap


PY_TYPE_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array",
}

class FunctionTools:
    def __init__(self, functions: List[Any] = []) -> None:
        self.functions = functions
        # 预先解析并缓存结果，避免重复 inspect
        self._tools: List[Dict[str, Any]] = [
            self.build_tool_from_function(fn) for fn in self.functions
        ]

    @classmethod
    def build_tool_from_function(cls, fn: Any) -> Dict[str, Any]:
        """从单个函数构建一个 OpenAI tool 定义。"""
        params_schema = cls._build_parameters_schema(fn)
        raw_doc = (fn.__doc__ or "").strip()
        first_line = ""
        if raw_doc:
            for line in raw_doc.splitlines():
                line = line.strip().lower()
                if not line:
                    continue
                # 跳过 Args/Arguments 段标题
                if line.startswith("args:") or line.startswith("arguments:"):
                    first_line = None
                    break
                first_line = line
                break
        if not first_line:
            # 对于没有 docstring 或只有参数段的函数，提供一个退化描述
            first_line = f"Auto-generated tool for function `{fn.__name__}`"

        return {
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": first_line,
                "parameters": params_schema,
            },
        }

    @staticmethod
    def _parse_param_docs(doc: str) -> Dict[str, str]:
        """从 docstring 中解析 Args/Arguments 段的参数说明。"""
        if not doc:
            return {}
        doc = textwrap.dedent(doc)
        lines = doc.splitlines()
        param_docs: Dict[str, str] = {}
        in_args = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("Args:") or stripped.startswith("Arguments:"):
                in_args = True
                continue
            if in_args:
                # 形如:  name: 描述...
                if ":" in stripped:
                    name, desc = stripped.split(":", 1)
                    param_docs[name.strip()] = desc.strip()
                # 碰到缩进不对/新的 section 就结束
                if not line.startswith("    ") and not line.startswith("\t"):
                    in_args = False
        return param_docs

    @classmethod
    def _build_parameters_schema(cls, fn: Any) -> Dict[str, Any]:
        sig = inspect.signature(fn)
        doc = fn.__doc__ or ""
        param_docs = cls._parse_param_docs(doc)

        properties: Dict[str, Any] = {}
        required: List[str] = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            # 类型映射
            annotation = param.annotation
            json_type = "string"
            if annotation in PY_TYPE_TO_JSON:
                json_type = PY_TYPE_TO_JSON[annotation]
            # 描述
            desc = param_docs.get(name, "")
            prop: Dict[str, Any] = {"type": json_type}
            if desc:
                prop["description"] = desc
            properties[name] = prop

            if param.default is inspect._empty:
                required.append(name)

        schema: Dict[str, Any] = {"type": "object"}
        if properties:
            schema["properties"] = properties
        if required:
            schema["required"] = required
        return schema

    @property
    def tools(self) -> List[Dict[str, Any]]:
        """返回基于函数与 docstring 解析出的 OpenAI tools 列表。"""
        return self._tools

    def __repr__(self) -> str:
        """以更友好的文本格式展示每个函数的解析结果。"""
        lines: List[str] = []
        for idx, tool in enumerate(self._tools, start=1):
            fn_meta = tool.get("function", {})
            name = fn_meta.get("name", "<unknown>")
            desc = fn_meta.get("description", "").strip()
            params = fn_meta.get("parameters", {})
            properties: Dict[str, Any] = params.get("properties", {}) or {}
            required = set(params.get("required", []) or [])

            lines.append(f"[{idx}] Function: {name}")
            if desc:
                lines.append(f"    Description: {desc}")
            if properties:
                lines.append("    Parameters:")
                for pname, meta in properties.items():
                    ptype = meta.get("type", "string")
                    pdesc = meta.get("description", "")
                    req_flag = "required" if pname in required else "optional"
                    # 形如:      - x (integer, required): 描述
                    header = f"      - {pname} ({ptype}, {req_flag})"
                    if pdesc:
                        header += f": {pdesc}"
                    lines.append(header)
            else:
                lines.append("    Parameters: (none)")

            lines.append("")  # 空行分隔函数

        return "\n".join(lines).rstrip()

    def call(self, function_name: str, function_args: dict) -> Any:
        """调用已注册的函数工具。"""
        for fn in self.functions:
            if fn.__name__ == function_name:
                return fn(**function_args)
        raise ValueError(f"Function '{function_name}' not found in registered tools.")
    
    def __str__(self) -> str:
        return self.__repr__()
    

