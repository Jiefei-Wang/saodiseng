from llm_output_parser import parse_json
import json

from modules.paper_search import search_papers

def json_list_to_list(json_list_str: str) -> list:
    list_of_list = [parse_json(response) for response in json_list_str]
    list_item = [item for sublist in list_of_list for item in sublist]
    dedup_list = list(set(list_item)) 
    return dedup_list

def search_papers_tool(query: str) -> list:
    """搜索学术论文， 返回标题，作者信息，摘要。

    Args:
        query: 搜索关键词
    """
    res = search_papers(query, per_page=10, page=1)
    res_json = json.dumps(res, ensure_ascii=False)
    return res_json

def combine_list_items(target_list, source_list):
    target_list_copy = target_list.copy()
    for x in target_list_copy:
        for y in source_list:
            if x['index'] == y['index']:
                x.update(y)
                break
    return target_list_copy