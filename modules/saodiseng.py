import os
import json
from modules.saodiseng_core import get_professor_papers, get_professor_list, deduplicate_papers, confirm_professor_papers








def retrieve_professor_papers(agent, school_name, department_name, professor_name):
    if not os.path.exists('data/professors'):
        os.makedirs('data/professors')
    professor_papers = get_professor_papers(agent, school_name, department_name, professor_name)
    
    dedup_papers = deduplicate_papers(agent, professor_papers)
    
    confirm_df = confirm_professor_papers(agent, school_name, department_name, professor_name, dedup_papers)

    data = confirm_df.to_dict(orient='records')
    filepath = f'data/professors/{school_name}_{department_name}_{professor_name}.json'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
    
    return confirm_df
