import wikipediaapi
from tqdm import tqdm
import pandas as pd

from modules.data import get_schools

wiki_wiki = wikipediaapi.Wikipedia(user_agent='saodiseng (saodiseng@gmail.com)', language='zh')
school_names = get_schools()
school_wiki = []
for name in tqdm(school_names):
    page = wiki_wiki.page(name)
    school_wiki.append(page.text)


df = pd.DataFrame({'school_name': school_names, 'wiki_text': school_wiki})

# how many rows have non-empty wiki_text
df['wiki_text'].apply(lambda x: len(x.strip()) > 0).sum()
df.to_feather('output/school_wiki.feather')



