
import requests
import json
import os
from llm_output_parser import parse_json




def _search_web_serper(keyword: str, page = 1) -> str:
    url = "https://google.serper.dev/search"
    payload = json.dumps({
      "q": keyword,
      "gl": "cn",
      "location": "China",
      "hl": "zh-cn",
      "page": page
    })
    headers = {
      'X-API-KEY': os.getenv("SERPER_KEY"),
      'Content-Type': 'application/json'
    }

    serper_response = requests.request("POST", url, headers=headers, data=payload)
    return parse_json(serper_response.text)

def search_web_serper(key: str, result_num = 10) -> list:
    """
    使用 SerperAPI 在网络上搜索。

    Args:
        key: 搜索关键词
        result_num: 需要返回的结果数量，默认为10
    """
    results = []
    page = 1
    while len(results) < result_num:
        response = _search_web_serper(key, page)
        if 'organic' in response:
            results.extend(response['organic'])
        else:
            break
        page += 1

    return results