import requests
import json
import os
import dotenv
import pandas as pd
from llm_output_parser import parse_json

from modules.ToolAgent import ToolAgent
from modules.html_conversion import html_to_markdown, get_web_contents
from modules.web_search import search_web_serper
from modules.paper_search import search_papers
from modules.FunctionTools import FunctionTools
from modules.utils import search_papers_tool, combine_list_items
from modules.saodiseng_core import get_professor_list, get_professor_papers, deduplicate_papers, confirm_professor_papers
from modules.saodiseng import retrieve_professor_papers


dotenv.load_dotenv()
with open('llm.py') as f:
    exec(f.read())



tools = FunctionTools([search_papers_tool])
agent = ToolAgent(client=client, model_name=model_name, tools=tools, temperature=0)


################################
# 给定大学和部门，确认教授列表并保存
################################
school_name = "江苏科技大学"
department_name = "材料科学与工程学院"
# professor_name = '郭伟'

def retrieve_professors(agent, school_name, department_name):
    professor_list = get_professor_list(agent, school_name, department_name)
    professor_list.to_json(f'data/departments/{school_name}_{department_name}.json', orient='records', force_ascii=False, indent=2)
    return professor_list



professor_list = retrieve_professors(agent, school_name, department_name)

professor_list = pd.read_json(f'data/departments/{school_name}_{department_name}.json')

professor_name = professor_list.iloc[0]['name']
professor_papers = get_professor_papers(agent, school_name, department_name, professor_name)

dedup_papers = deduplicate_papers(agent, professor_papers)

confirm_df = confirm_professor_papers(agent, school_name, department_name, professor_name, dedup_papers)




df = retrieve_professor_papers(school_name, department_name, professor_name)


from modules.pdf_coversion import process_pdf_url
url = 'https://hj.hwi.com.cn/cn/article/pdf/preview/20170203.pdf'
res= process_pdf_url(url)