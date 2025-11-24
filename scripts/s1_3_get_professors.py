import requests
import json
import os
import dotenv
import pandas as pd
import re
import html

from modules.html_conversion import html_to_markdown


with open('scripts/agent_func.py') as f:
    exec(f.read())
    

dotenv.load_dotenv()



df = pd.read_feather('output/school_wiki.feather')

df[df.school_name=="江苏科技大学"].wiki_text.to_list()[0]




# rest request to https://zh.wikipedia.org/wiki/江苏科技大学
response = requests.get("https://zh.wikipedia.org/wiki/江苏科技大学",
                    headers={
                           "User-Agent": "saodiseng (saodiseng@gmail.com)"
                       })

# Convert to markdown
markdown_text = html_to_markdown(response.text)







# read school departments
school_name = "江苏科技大学"
with open(f'output/schools/{school_name}.json', 'r', encoding='utf-8') as f:
    department = json.load(f)






url = "https://google.serper.dev/search"

payload = json.dumps({
  "q": "apple inc"
})
headers = {
  'X-API-KEY': os.getenv("SERPER_KEY"),
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)