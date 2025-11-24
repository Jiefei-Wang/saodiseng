
from turtle import pd
import json
from llm_output_parser import parse_json
import pandas as pd

from modules.utils import json_list_to_list, combine_list_items
from modules.web_search import search_web_serper
from modules.html_conversion import get_web_contents



def get_professor_list(agent, school_name, department_name, verbose=True):
    serper_result = search_web_serper(f"{school_name} {department_name} 师资 教授")
    links = [item['link'] for item in serper_result]

    # request web contents
    department_contents = get_web_contents(links)


    with open('prompts/extract_professor.txt', 'r', encoding='utf-8') as f:
        professor_template = f.read()

    prompt_list = [professor_template.replace("{school}", f"学校：{school_name} 学院：{department_name}").replace("{content}", department_contents[i]) for i in range(len(department_contents))]

    responses, histories = agent.batch_chat(prompt_list, verbose=verbose, use_tools=False)

    professor_list = [parse_json(response) for response in responses]
    professor_dict = {}
    for i, professors in enumerate(professor_list):
        for professor in professors:
            if professor not in professor_dict:
                professor_dict[professor] = {
                    'link': links[i]
                }
    
    professor_dict_df = pd.DataFrame([{'name': k, **v} for k, v in professor_dict.items()])
    return professor_dict_df





##############################################
## Get professor papers
##############################################
def get_professor_papers(agent, school_name, department_name, professor_name, result_num=20, verbose=True, content_size = 40000):
    serper_result = search_web_serper(f"{school_name} {department_name} {professor_name} 论文", result_num=result_num)

    links = [item['link'] for item in serper_result]

    web_contents = get_web_contents(links)
    web_contents = [content[:content_size] for content in web_contents]

    with open('prompts/extract_paper.txt', 'r', encoding='utf-8') as f:
        paper_template = f.read()

    paper_prompt_list = [paper_template.replace("{content}", web_contents[i]).replace("{person}", f"学校：{school_name} 学院：{department_name} 教授：{professor_name}") for i in range(len(web_contents))]

    responses, histories = agent.batch_chat(paper_prompt_list, verbose=verbose, use_tools=False)

    paper_list = [parse_json(response) for response in responses]
    # add source_index to each achievement
    for idx, achievement_sublist in enumerate(paper_list):
        for achievement in achievement_sublist:
            achievement['link'] = links[idx]

    paper_list = [i for lst in paper_list for i in lst]  # flatten list
    paper_list = [i for i in paper_list if i['name_confirm']=="yes"]
    paper_list = [i for i in paper_list if i['department_confirm']!="no"]
    paper_list = [i for i in paper_list if i['school_confirm']!="no"]
    paper_list = [i for i in paper_list if i['paper_confirm']=="yes"]


    paper_list_df = pd.DataFrame(paper_list)
    paper_list_df.drop(columns=['name_confirm', 'paper_confirm', 'paper_confirm'], inplace=True, errors='ignore')
    
    return paper_list_df


def deduplicate_papers(agent, paper_list_df, verbose=True):
    with open('prompts/dedup_paper.txt', 'r', encoding='utf-8') as f:
        dedup_paper_template = f.read()
    
    paper_list = paper_list_df.to_dict(orient='records')
    paper_list = [{**item, 'index': idx} for idx, item in enumerate(paper_list)]
    
    paper_list_copy = [
        {'type': item['type'], 'value': item['value'], 'paper_body': item['paper_body'], 'index': item['index']} for item in paper_list
        ]
    paper_prompt = dedup_paper_template.replace("{content}", json.dumps(paper_list_copy, ensure_ascii=False))

    dedup_response, history = agent.chat(paper_prompt, verbose=verbose, use_tools=False)

    dedup_papers = parse_json(dedup_response)
    dedup_papers = combine_list_items(dedup_papers, paper_list)
    dedup_papers_df = pd.DataFrame(dedup_papers)
    dedup_papers_df.drop(columns=['index'], inplace=True, errors='ignore')
    
    return dedup_papers_df



##############################################
## confirm the achievements
##############################################
def confirm_professor_papers(agent, school_name, department_name, professor_name, dedup_papers_df, verbose=True):
    with open('prompts/confirm_professor_papers.txt', 'r', encoding='utf-8') as f:
        confirm_professor_papers_template = f.read()

    
    dedup_papers = dedup_papers_df.to_dict(orient='records')
    dedup_papers = [{**item, 'index': idx} for idx, item in enumerate(dedup_papers)]
    
    # copy dedup_achievements and keep only type and value keys
    dedup_papers_copy = [{'type': item['type'], 'value': item['value'], 'index': item['index']} for item in dedup_papers]
    confirm_paper_prompt = confirm_professor_papers_template.replace("{professor_name}", professor_name).replace("{department}", department_name).replace("{school}", school_name).replace("{papers}", str(dedup_papers_copy))

    confirm_response, history = agent.chat(confirm_paper_prompt, verbose=verbose)

    confirm_response_list = parse_json(confirm_response)
    confirm_response_list = combine_list_items(confirm_response_list, dedup_papers)
    confirm_df = pd.DataFrame(confirm_response_list)
    return confirm_df