
import requests

def fetch_openalex_works(query, per_page=20, page=1, email="youremail@example.com"):
    """ 查询 OpenAlex works，返回 JSON """
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": per_page,
        "page": page,
        "mailto": email
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("results", [])


def reconstruct_abstract(index_obj):
    """ 将 OpenAlex abstract_inverted_index 解析为纯文本 """
    if not index_obj:
        return None
    words = []
    for word, positions in index_obj.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return " ".join([w[1] for w in words])


def parse_work_item(item):
    """ 从单个 work 项中提取 title, authors, abstract """
    title = item.get("display_name")

    # 处理作者
    authors_raw = item.get("authorships", [])
    authors = []
    for a in authors_raw:
        # 使用 raw_author_name，如果没有则回退到 display_name
        name = a.get("raw_author_name") or a.get("author", {}).get("display_name")
        # affiliation String（第一个单位）
        aff = None
        if a.get("institutions"):
            aff = a["institutions"][0].get("display_name")
        authors.append({
            "name": name,
            "affiliation": aff
        })

    # 摘要（倒排索引转纯文本）
    abstract = reconstruct_abstract(item.get("abstract_inverted_index"))

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract
    }


def search_papers(query, per_page=20, page=1):
    """ 
    返回 list of dict，每个 dict 包含 title, authors(list), abstract 
    
    Args:
        query: 搜索关键词
        per_page: 每页结果数量，默认20
        page: 页码，默认1
    """
    items = fetch_openalex_works(query, per_page, page)
    return [parse_work_item(it) for it in items]
