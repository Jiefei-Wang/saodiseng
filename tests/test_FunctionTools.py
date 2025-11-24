import unittest

from modules.FunctionTools import FunctionTools


def search_web(key: str) -> str:
    """使用 SerpAPI 在网络上搜索。"""
    raise NotImplementedError


def browse_web(url: str) -> str:
    """获取指定网页的内容。"""
    raise NotImplementedError


def func_no_doc(x):
    return x + 1


def func_with_doc(x: int, y: str) -> str:
    """
Args:
     x: 一个整数参数
    y: 一个字符串参数
    """
    return f"{y} repeated {x} times is: " + (y * x)


class TestFunctionTools(unittest.TestCase):
    def test_tools_length(self) -> None:
        tools = FunctionTools([search_web, browse_web, func_no_doc, func_with_doc])
        self.assertEqual(len(tools.tools), 4)

    def test_search_web_schema(self) -> None:
        tools = FunctionTools([search_web])
        tool = tools.tools[0]
        fn = tool["function"]
        self.assertEqual(fn["name"], "search_web")
        params = fn["parameters"]
        self.assertEqual(params["type"], "object")
        self.assertIn("key", params["properties"])
        self.assertEqual(params["properties"]["key"]["type"], "string")
        self.assertIn("key", params["required"])

    def test_func_no_doc_has_fallback_description(self) -> None:
        tools = FunctionTools([func_no_doc])
        desc = tools.tools[0]["function"]["description"]
        self.assertIn("func_no_doc", desc)

    def test_func_with_doc_param_docs(self) -> None:
        tools = FunctionTools([func_with_doc])
        fn = tools.tools[0]["function"]
        params = fn["parameters"]
        props = params["properties"]
        # 类型来自注解
        self.assertEqual(props["x"]["type"], "integer")
        self.assertEqual(props["y"]["type"], "string")
        # 描述来自 Args 段
        self.assertIn("一个整数参数", props["x"].get("description", ""))
        self.assertIn("一个字符串参数", props["y"].get("description", ""))

    def test_repr_contains_function_names(self) -> None:
        tools = FunctionTools([search_web, browse_web])
        s = repr(tools)
        self.assertIn("Function: search_web", s)
        self.assertIn("Function: browse_web", s)


if __name__ == "__main__":
    unittest.main()
