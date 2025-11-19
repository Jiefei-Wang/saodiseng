import pandas as pd
from tqdm import tqdm
from llm_output_parser import parse_json
import json
import os

context_char = 20000
with open('llm.py') as f:
    exec(f.read())

# Load the agent functions and tools
with open('scripts/agent_func.py') as f:
    exec(f.read())

df = pd.read_feather('output/school_wiki.feather')

# prompts/department_extract.txt
with open('prompts/department_extract.txt', 'r', encoding='utf-8') as f:
    department_extract_tmp = f.read()


if False:
    row0 = df.iloc[0]
    prompt = department_extract_tmp.replace("{wiki_content}", row0['wiki_text'])
    response, history = query_agent(prompt, verbose=True)



# create folder output/schools if not exists
if not os.path.exists('output/schools'):
    os.makedirs('output/schools')
    
for idx, row in tqdm(df.iterrows(), total=len(df)):
    wiki_text = row['wiki_text']
    if len(wiki_text.strip()) == 0:
        continue
    # split wiki_text into chunks of `context_char` characters
    wiki_chunks = [wiki_text[i:i+context_char] for i in range(0, len(wiki_text), context_char)]
    
    response_list = []
    for chunk in wiki_chunks:
        prompt = department_extract_tmp.replace("{wiki_content}", chunk)
        response, history = query_agent(prompt, verbose=False)
        chunk_response_list = parse_json(response)
        response_list.extend(chunk_response_list)

    response_list = list(set(response_list))

    if not response_list:
        print(f"Failed to parse JSON for {row['school_name']}")
        continue
    
    response_json = json.dumps(response_list, ensure_ascii=False, indent=2)
    # save response to output/schools/{school_name}.json
    school_name = row['school_name'].replace('/', '_')  # replace / with _
    with open(f'output/schools/{school_name}.json', 'w', encoding='utf-8') as f:
        f.write(response_json)